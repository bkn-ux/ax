"""AX 인재 서치 시장 - 탐색적 데이터 분석 (EDA)
주의: 공개 통계가 아니라, 서치펌 의사결정 논리를 검증하기 위한 '시뮬레이션 데이터셋'(seed 고정)이다.
"""
import json, numpy as np, pandas as pd
rng = np.random.default_rng(2027)
N = 480
ind = rng.choice(["제조","금융","유통·커머스","IT·플랫폼","바이오·헬스","에너지·화학","공공·교육"], N,
                 p=[.22,.17,.14,.18,.10,.12,.07])
size = rng.choice(["대기업","중견","중소"], N, p=[.25,.35,.40])
stage = rng.choice([0,1,2,3], N, p=[.27,.38,.24,.11])  # 0 인식 1 PoC 2 확산 3 내재화
ind_prem = {"IT·플랫폼":1.0,"금융":.85,"바이오·헬스":.7,"제조":.5,"유통·커머스":.6,"에너지·화학":.45,"공공·교육":.2}
base = np.array([ind_prem[i] for i in ind])
sz = pd.Series(size).map({"대기업":1.0,"중견":.6,"중소":.3}).values
vac = np.clip(np.round(rng.poisson(1+ 6*sz*(0.4+0.4*stage/3+0.3*base)) ),0,None)
ttf = np.round(55 + 18*(stage==3)*0 + 14*base + 10*(size=="중소") + rng.normal(0,9,N) + 6*(stage>=2)).astype(int)
ws = np.round(np.clip(rng.lognormal(3.6,.7,N)*(0.4+sz),5,900)).astype(int)  # 연간 AI교육/워크숍 지출(백만원)
gap = np.clip(np.round(30+ 12*stage + 10*base + rng.normal(0,10,N)),5,98)    # 리더십 공백 지수
prem = np.round(np.clip(8 + 14*base + 5*stage + rng.normal(0,5,N),0,45),1)      # AI 리더 연봉 프리미엄 %
ws_roi = np.clip(np.round(35 - 7*(ws>150) + 4*stage + rng.normal(0,10,N)),0,90)   # 교육 후 6개월 내 현업 적용률 %
df = pd.DataFrame(dict(industry=ind,size=size,stage=stage,ai_vacancy=vac,time_to_fill_days=ttf,
                       workshop_spend_mkrw=ws,leadership_gap=gap,salary_premium_pct=prem,workshop_apply_rate=ws_roi))
df.to_csv("ax_market_sim.csv",index=False,encoding="utf-8-sig")

out={}
out["n"]=N
out["stage_share"]=df.stage.value_counts(normalize=True).sort_index().round(3).tolist()
g=df.groupby("industry").agg(vac=("ai_vacancy","mean"),ttf=("time_to_fill_days","mean"),prem=("salary_premium_pct","mean"),gap=("leadership_gap","mean")).round(1).sort_values("prem",ascending=False)
out["industry"]=[dict(name=k,**v) for k,v in g.to_dict("index").items()]
s=df.groupby("stage").agg(gap=("leadership_gap","mean"),apply=("workshop_apply_rate","mean"),ttf=("time_to_fill_days","mean"),ws=("workshop_spend_mkrw","median"),vac=("ai_vacancy","mean")).round(1)
out["stage"]=s.reset_index().to_dict("records")
out["corr"]={ "gap~apply":round(df.leadership_gap.corr(df.workshop_apply_rate),2),
              "spend~apply":round(df.workshop_spend_mkrw.corr(df.workshop_apply_rate),2),
              "stage~ttf":round(df.stage.corr(df.time_to_fill_days),2),
              "stage~prem":round(df.stage.corr(df.salary_premium_pct),2),
              "gap~vac":round(df.leadership_gap.corr(df.ai_vacancy),2)}
out["spend_bins"]=[]
for lo,hi in [(0,30),(30,60),(60,120),(120,250),(250,2000)]:
    m=df[(df.workshop_spend_mkrw>=lo)&(df.workshop_spend_mkrw<hi)]
    out["spend_bins"].append(dict(label=f"{lo}~{hi if hi<2000 else ''}",n=len(m),apply=round(m.workshop_apply_rate.mean(),1)))
out["scatter"]=df.sample(140,random_state=1)[["leadership_gap","workshop_apply_rate","stage"]].round(1).values.tolist()
sz_=df.groupby("size").agg(ttf=("time_to_fill_days","mean"),prem=("salary_premium_pct","mean"),vac=("ai_vacancy","mean"),ws=("workshop_spend_mkrw","median")).round(1)
out["size"]=sz_.reset_index().to_dict("records")
# 타깃 세그먼트: 확산기(2) 이상 + 공백 높음 + 공석 있음
tg=df[(df.stage>=2)&(df.leadership_gap>=60)&(df.ai_vacancy>=2)]
out["target_share"]=round(len(tg)/N*100,1)
out["target_by_size"]=tg["size"].value_counts().to_dict()
out["target_by_ind"]=tg.industry.value_counts().head(3).to_dict()
out["desc"]=df.describe().round(1).to_dict()
json.dump(out,open("eda.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1)[:3500])
