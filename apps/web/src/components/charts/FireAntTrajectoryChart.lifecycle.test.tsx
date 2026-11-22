// @vitest-environment jsdom
import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import type { PredictionResponse } from '@/lib/types';
import { buildTrajectory } from '@/lib/predictionTrajectory';

type MockSeries = {
  setData: ReturnType<typeof vi.fn>;
  applyOptions: ReturnType<typeof vi.fn>;
  createPriceLine: ReturnType<typeof vi.fn>;
  removePriceLine: ReturnType<typeof vi.fn>;
  options: Record<string,unknown>;
};

const mocks = vi.hoisted(() => ({ charts: [] as Array<{
  remove: ReturnType<typeof vi.fn>;
  series: MockSeries[];
  fitContent: ReturnType<typeof vi.fn>;
}> }));
vi.mock('lightweight-charts', () => ({
  AreaSeries: 'area', CandlestickSeries: 'candle', HistogramSeries: 'volume', LineSeries: 'line',
  ColorType: { Solid:'solid' }, LineStyle: { Dashed:2 }, LineType: { Curved:2 },
  createChart: () => {
    const chart = {
      series: [] as MockSeries[],
      remove: vi.fn(), fitContent:vi.fn(), applyOptions:vi.fn(), subscribeCrosshairMove:vi.fn(),
      priceScale: () => ({ applyOptions:vi.fn() }),
      timeScale: () => ({ fitContent:chart.fitContent }),
      addSeries: (_type:unknown, options:Record<string,unknown>) => {
        const series = { setData:vi.fn(), applyOptions:vi.fn(), options,
          createPriceLine:vi.fn((line:unknown)=>line), removePriceLine:vi.fn() };
        chart.series.push(series); return series;
      },
    };
    mocks.charts.push(chart); return chart;
  },
}));
import { FireAntTrajectoryChart } from './FireAntTrajectoryChart';

afterEach(() => { cleanup(); mocks.charts.length=0; vi.restoreAllMocks(); });
const bar={date:'2026-11-20',open:50,high:51,low:49,close:50,volume:100};
const prediction={symbol:'VIC',model_type:'lightgbm',current_price:50,predicted_label:2,class_name:'TĂNG',
  probabilities:{'GIẢM':.2,'ĐI NGANG':.3,'TĂNG':.5}, date:bar.date,data_as_of_date:bar.date,
  trajectory:['2026-11-23','2026-11-24','2026-11-25'].map((date,i)=>({date,day_offset:i+1,
    day_name:`T+${i+1}`,predicted_trend:'TĂNG',confidence:.5,
    probabilities:{'GIẢM':.2,'ĐI NGANG':.3,'TĂNG':.5},signal:'MUA',note:''}))} as PredictionResponse;

it('repopulates recreated charts and releases every resize listener on unmount', () => {
  const add=vi.spyOn(window,'addEventListener'), remove=vi.spyOn(window,'removeEventListener');
  const props={symbol:'VIC',modelType:'lightgbm' as const,bars:[bar],prediction};
  const view=render(<FireAntTrajectoryChart {...props} height={460}/>);
  for(const height of [300,600,460]) view.rerender(<FireAntTrajectoryChart {...props} height={height}/>);
  for(const chart of mocks.charts) {
    expect(chart.series[0].options.priceFormat).toEqual({type:'price',precision:2,minMove:.01});
    expect(chart.series[0].setData).toHaveBeenCalledWith([expect.objectContaining({time:bar.date,close:50})]);
    expect(chart.series[5].setData).toHaveBeenCalledWith(expect.arrayContaining([
      expect.objectContaining({time:'2026-11-25'}),
    ]));
    expect(chart.series[5].options).toMatchObject({lastValueVisible:false,priceLineVisible:false,title:''});
    expect(chart.series[5].createPriceLine).toHaveBeenLastCalledWith(expect.objectContaining({
      price:buildTrajectory(prediction,'VIC','lightgbm',bar)[3].price,title:'Minh hoạ T+3',axisLabelVisible:true,
    }));
  }
  view.unmount();
  expect(mocks.charts).toHaveLength(4);
  for(const chart of mocks.charts) expect(chart.remove).toHaveBeenCalledTimes(1);
  const resizeHandlers=add.mock.calls.filter(([type])=>type==='resize').map(([,handler])=>handler);
  expect(resizeHandlers).toHaveLength(4);
  for(const handler of resizeHandlers) expect(remove).toHaveBeenCalledWith('resize',handler);
});

it('toggles illustration without creating series or resetting the viewed time range', () => {
  render(<FireAntTrajectoryChart symbol="VIC" modelType="lightgbm" bars={[bar]} prediction={prediction}/>);
  const chart=mocks.charts[0]; const initialFits=chart.fitContent.mock.calls.length;
  fireEvent.click(screen.getByRole('button',{name:'Kịch bản minh họa (T+1 → T+3)'}));
  expect(chart.series[5].applyOptions).toHaveBeenLastCalledWith({visible:false});
  fireEvent.click(screen.getByRole('button',{name:'Kịch bản minh họa (T+1 → T+3)'}));
  expect(chart.series[5].applyOptions).toHaveBeenLastCalledWith({visible:true});
  expect(chart.fitContent).toHaveBeenCalledTimes(initialFits);
  expect(mocks.charts).toHaveLength(1); expect(chart.series).toHaveLength(6);
});

it('replaces the T+3 price marker when forecast changes instead of accumulating markers',()=>{
  const props={symbol:'VIC',modelType:'lightgbm' as const,bars:[bar],prediction};
  const view=render(<FireAntTrajectoryChart {...props}/>);
  const series=mocks.charts[0].series[5];
  const oldLine=series.createPriceLine.mock.results[0].value;
  const changed={...prediction,trajectory:prediction.trajectory!.map(s=>({...s,confidence:.8}))};
  view.rerender(<FireAntTrajectoryChart {...props} prediction={changed}/>);
  expect(series.removePriceLine).toHaveBeenCalledExactlyOnceWith(oldLine);
  expect(series.createPriceLine).toHaveBeenCalledTimes(2);
  expect(series.createPriceLine).toHaveBeenLastCalledWith(expect.objectContaining({
    price:buildTrajectory(changed,'VIC','lightgbm',bar)[3].price,
  }));
});
