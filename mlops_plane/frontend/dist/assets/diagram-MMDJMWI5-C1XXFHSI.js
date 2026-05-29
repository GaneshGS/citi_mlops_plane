import{Bt as e,Gt as t,Ht as n,Lt as r,Ut as i,V as a,Wt as o,Yt as s,in as c,on as l,qt as u,rn as d,vn as f,vt as p,yn as m}from"./index-JhL5eZG-.js";import{t as h}from"./chunk-4BX2VUAB-DfOb9rPE.js";import{t as g}from"./mermaid-parser.core-JYH_dHJI.js";var _={showLegend:!0,ticks:5,max:null,min:0,graticule:`circle`},v={axes:[],curves:[],options:_},y=structuredClone(v),b=n.radar,x=f(()=>a({...b,...t().radar}),`getConfig`),S=f(()=>y.axes,`getAxes`),C=f(()=>y.curves,`getCurves`),w=f(()=>y.options,`getOptions`),T=f(e=>{y.axes=e.map(e=>({name:e.name,label:e.label??e.name}))},`setAxes`),E=f(e=>{y.curves=e.map(e=>({name:e.name,label:e.label??e.name,entries:D(e.entries)}))},`setCurves`),D=f(e=>{if(e[0].axis==null)return e.map(e=>e.value);let t=S();if(t.length===0)throw Error(`Axes must be populated before curves for reference entries`);return t.map(t=>{let n=e.find(e=>e.axis?.$refText===t.name);if(n===void 0)throw Error(`Missing entry for axis `+t.label);return n.value})},`computeCurveEntries`),O={getAxes:S,getCurves:C,getOptions:w,setAxes:T,setCurves:E,setOptions:f(e=>{let t=e.reduce((e,t)=>(e[t.name]=t,e),{});y.options={showLegend:t.showLegend?.value??_.showLegend,ticks:t.ticks?.value??_.ticks,max:t.max?.value??_.max,min:t.min?.value??_.min,graticule:t.graticule?.value??_.graticule}},`setOptions`),getConfig:x,clear:f(()=>{r(),y=structuredClone(v)},`clear`),setAccTitle:c,getAccTitle:o,setDiagramTitle:l,getDiagramTitle:u,getAccDescription:i,setAccDescription:d},k=f(e=>{h(e,O);let{axes:t,curves:n,options:r}=e;O.setAxes(t),O.setCurves(n),O.setOptions(r)},`populate`),A={parse:f(async e=>{let t=await g(`radar`,e);m.debug(t),k(t)},`parse`)},j=f((e,t,n,r)=>{let i=r.db,a=i.getAxes(),o=i.getCurves(),s=i.getOptions(),c=i.getConfig(),l=i.getDiagramTitle(),u=M(p(t),c),d=s.max??Math.max(...o.map(e=>Math.max(...e.entries))),f=s.min,m=Math.min(c.width,c.height)/2;N(u,a,m,s.ticks,s.graticule),P(u,a,m,c),F(u,a,o,f,d,s.graticule,c),R(u,o,s.showLegend,c),u.append(`text`).attr(`class`,`radarTitle`).text(l).attr(`x`,0).attr(`y`,-c.height/2-c.marginTop)},`draw`),M=f((t,n)=>{let r=n.width+n.marginLeft+n.marginRight,i=n.height+n.marginTop+n.marginBottom,a={x:n.marginLeft+n.width/2,y:n.marginTop+n.height/2};return e(t,i,r,n.useMaxWidth??!0),t.attr(`viewBox`,`0 0 ${r} ${i}`),t.append(`g`).attr(`transform`,`translate(${a.x}, ${a.y})`)},`drawFrame`),N=f((e,t,n,r,i)=>{if(i===`circle`)for(let t=0;t<r;t++){let i=n*(t+1)/r;e.append(`circle`).attr(`r`,i).attr(`class`,`radarGraticule`)}else if(i===`polygon`){let i=t.length;for(let a=0;a<r;a++){let o=n*(a+1)/r,s=t.map((e,t)=>{let n=2*t*Math.PI/i-Math.PI/2;return`${o*Math.cos(n)},${o*Math.sin(n)}`}).join(` `);e.append(`polygon`).attr(`points`,s).attr(`class`,`radarGraticule`)}}},`drawGraticule`),P=f((e,t,n,r)=>{let i=t.length;for(let a=0;a<i;a++){let o=t[a].label,s=2*a*Math.PI/i-Math.PI/2;e.append(`line`).attr(`x1`,0).attr(`y1`,0).attr(`x2`,n*r.axisScaleFactor*Math.cos(s)).attr(`y2`,n*r.axisScaleFactor*Math.sin(s)).attr(`class`,`radarAxisLine`),e.append(`text`).text(o).attr(`x`,n*r.axisLabelFactor*Math.cos(s)).attr(`y`,n*r.axisLabelFactor*Math.sin(s)).attr(`class`,`radarAxisLabel`)}},`drawAxes`);function F(e,t,n,r,i,a,o){let s=t.length,c=Math.min(o.width,o.height)/2;n.forEach((t,n)=>{if(t.entries.length!==s)return;let l=t.entries.map((e,t)=>{let n=2*Math.PI*t/s-Math.PI/2,a=I(e,r,i,c);return{x:a*Math.cos(n),y:a*Math.sin(n)}});a===`circle`?e.append(`path`).attr(`d`,L(l,o.curveTension)).attr(`class`,`radarCurve-${n}`):a===`polygon`&&e.append(`polygon`).attr(`points`,l.map(e=>`${e.x},${e.y}`).join(` `)).attr(`class`,`radarCurve-${n}`)})}f(F,`drawCurves`);function I(e,t,n,r){return r*(Math.min(Math.max(e,t),n)-t)/(n-t)}f(I,`relativeRadius`);function L(e,t){let n=e.length,r=`M${e[0].x},${e[0].y}`;for(let i=0;i<n;i++){let a=e[(i-1+n)%n],o=e[i],s=e[(i+1)%n],c=e[(i+2)%n],l={x:o.x+(s.x-a.x)*t,y:o.y+(s.y-a.y)*t},u={x:s.x-(c.x-o.x)*t,y:s.y-(c.y-o.y)*t};r+=` C${l.x},${l.y} ${u.x},${u.y} ${s.x},${s.y}`}return`${r} Z`}f(L,`closedRoundCurve`);function R(e,t,n,r){if(!n)return;let i=(r.width/2+r.marginRight)*3/4,a=-(r.height/2+r.marginTop)*3/4;t.forEach((t,n)=>{let r=e.append(`g`).attr(`transform`,`translate(${i}, ${a+n*20})`);r.append(`rect`).attr(`width`,12).attr(`height`,12).attr(`class`,`radarLegendBox-${n}`),r.append(`text`).attr(`x`,16).attr(`y`,0).attr(`class`,`radarLegendText`).text(t.label)})}f(R,`drawLegend`);var z={draw:j},B=f((e,t)=>{let n=``;for(let r=0;r<e.THEME_COLOR_LIMIT;r++){let i=e[`cScale${r}`];n+=`
		.radarCurve-${r} {
			color: ${i};
			fill: ${i};
			fill-opacity: ${t.curveOpacity};
			stroke: ${i};
			stroke-width: ${t.curveStrokeWidth};
		}
		.radarLegendBox-${r} {
			fill: ${i};
			fill-opacity: ${t.curveOpacity};
			stroke: ${i};
		}
		`}return n},`genIndexStyles`),V=f(e=>{let n=a(s(),t().themeVariables);return{themeVariables:n,radarOptions:a(n.radar,e)}},`buildRadarStyleOptions`),H={parser:A,db:O,renderer:z,styles:f(({radar:e}={})=>{let{themeVariables:t,radarOptions:n}=V(e);return`
	.radarTitle {
		font-size: ${t.fontSize};
		color: ${t.titleColor};
		dominant-baseline: hanging;
		text-anchor: middle;
	}
	.radarAxisLine {
		stroke: ${n.axisColor};
		stroke-width: ${n.axisStrokeWidth};
	}
	.radarAxisLabel {
		dominant-baseline: middle;
		text-anchor: middle;
		font-size: ${n.axisLabelFontSize}px;
		color: ${n.axisColor};
	}
	.radarGraticule {
		fill: ${n.graticuleColor};
		fill-opacity: ${n.graticuleOpacity};
		stroke: ${n.graticuleColor};
		stroke-width: ${n.graticuleStrokeWidth};
	}
	.radarLegendText {
		text-anchor: start;
		font-size: ${n.legendFontSize}px;
		dominant-baseline: hanging;
	}
	${B(t,n)}
	`},`styles`)};export{H as diagram};