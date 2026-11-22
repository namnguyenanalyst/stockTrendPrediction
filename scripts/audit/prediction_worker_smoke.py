"""Exercise the actual worker in disposable containers against a local fake API."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import threading


def main():
    records = []
    status = [200]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            records.append({'path':self.path, 'payload':body,
                            'has_test_auth':self.headers.get('X-Internal-Worker-Secret') == 'isolated-test-only'})
            self.send_response(status[0]); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(json.dumps({'status':'success' if status[0]==200 else 'error',
                                        'message':'isolated fixture'}).encode())

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(('0.0.0.0',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    worker = Path('infra/scripts/retrain_worker.py').resolve()
    results = []
    try:
        for code in (200,503):
            status[0] = code
            command = ['docker','run','--rm','--env','INTERNAL_WORKER_SECRET=isolated-test-only',
                       '--mount',f'type=bind,src={worker},dst=/worker.py,readonly',
                       'python:3.11-alpine','python','/worker.py','--once','--api-url',
                       f'http://host.docker.internal:{server.server_port}']
            result = subprocess.run(command,capture_output=True,text=True,timeout=60)
            results.append({'fixture_http_status':code,'worker_exit_code':result.returncode,
                            'request':records[-1] if records else None})
            assert result.returncode == 0 if code == 200 else result.returncode != 0
        assert len(records)==2
        assert all(r['has_test_auth'] and r['path']=='/api/v1/predict/retrain' for r in records)
    finally:
        server.shutdown(); server.server_close()
    Path('reports/prediction-audit-2026-11-20/worker-container-smoke.json').write_text(
        json.dumps({'environment':'Disposable worker containers + local fake API; no production retrain',
                    'results':results},indent=2))
    print('worker container success + upstream failure verified; production artifacts untouched')


if __name__ == '__main__':
    main()
