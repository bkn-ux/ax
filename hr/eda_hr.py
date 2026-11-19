"""AX 교육·워크숍 HR 관점 EDA. 시뮬레이션 데이터(가상, seed 고정). 실제 통계가 아니다."""
import json, numpy as np, pandas as pd
rng = np.random.default_rng(2027)
N = 540
fam = rng.choice(["R&D·개발","영업·마케팅","생산·운영","재무·기획","HR·총무","CS·서비스"], N, p=[.22,.2,.2,.14,.08,.16])
lvl = rng.choice(["임원·팀장","실무자"], N, p=[.22,.78])
fmt = rng.choice(["강의형","실습형","업무적용형"], N, p=[.38,.34,.28])
sponsor = rng.choice([0,1], N, p=[.55,.45])           # 팀장/임원 후원 여부
hours = np.clip(np.round(rng.gamma(4, 4, N)),2,60)    # 교육 시간
base = {"강의형":22,"실습형":34,"업무적용형":47}
fam_adj = {"R&D·개발":8,"영업·마케팅":2,"생산·운영":-6,"재무·기획":3,"HR·총무":-1,"CS·서비스":1}
apply = np.array([base[f] for f in fmt]) + 17*sponsor + np.array([fam_adj[x] for x in fam]) \
        + 6*np.log1p(hours) - 0.08*hours + 4*(lvl=="임원·팀장") + rng.normal(0,7,N)
apply = np.clip(np.round(apply,1),3,95)
gain = np.clip(np.round(0.16*apply + 1.2*sponsor + rng.normal(0,2.2,N),1),0,25)   # 업무 시간 절감 %
gap = np.clip(np.round(rng.normal(55,14,N) + 8*(lvl=="임원·팀장") + np.array([ {"생산·운영":10,"HR·총무":6}.get(x,0) for x in fam]),1),10,95)
ttp = np.clip(np.round(60 - 0.35*apply + 0.4*gap/10*10*0.2 + rng.normal(0,8,N)),10,120)  # 숙련까지 일수
df = pd.DataFrame(dict(job_family=fam, level=lvl, format=fmt, sponsor=sponsor, hours=hours, apply_rate=apply,
                       time_saved_pct=gain, skill_gap=gap, days_to_proficiency=ttp))
df.to_csv("ax_hr_sim.csv", index=False, encoding="utf-8-sig")
o = {"n": N}
o["format"] = [dict(k=k, apply=round(v.apply_rate.mean(),1), n=len(v)) for k,v in df.groupby("format")]
o["format"].sort(key=lambda x: x["apply"])
o["sponsor"] = [dict(k=("후원 있음" if k else "후원 없음"), apply=round(v.apply_rate.mean(),1), saved=round(v.time_saved_pct.mean(),1), n=len(v)) for k,v in df.groupby("sponsor")]
bins = [(0,8),(8,16),(16,24),(24,40),(40,61)]
o["hours"] = [dict(k=f"{a}~{b}h", apply=round(df[(df.hours>=a)&(df.hours<b)].apply_rate.mean(),1), n=int(((df.hours>=a)&(df.hours<b)).sum())) for a,b in bins]
o["family"] = sorted([dict(k=k, apply=round(v.apply_rate.mean(),1), gap=round(v.skill_gap.mean(),1)) for k,v in df.groupby("job_family")], key=lambda x: -x["gap"])
o["level"] = [dict(k=k, apply=round(v.apply_rate.mean(),1), gap=round(v.skill_gap.mean(),1)) for k,v in df.groupby("level")]
o["corr"] = {"hours~apply": round(df.hours.corr(df.apply_rate),2), "sponsor~apply": round(df.sponsor.corr(df.apply_rate),2),
             "apply~saved": round(df.apply_rate.corr(df.time_saved_pct),2), "apply~days": round(df.apply_rate.corr(df.days_to_proficiency),2)}
o["scatter"] = df.sample(150, random_state=3)[["hours","apply_rate","sponsor"]].round(1).values.tolist()
hi = df[(df.apply_rate>=50)]
o["hi_share_by_format"] = {k: round((v.apply_rate>=50).mean()*100,1) for k,v in df.groupby("format")}
o["priority_share"] = round(((df.skill_gap>=65)&(df.sponsor==0)).mean()*100,1)   # 격차 큰데 후원 없는 팀
json.dump(o, open("eda_hr.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(o, ensure_ascii=False)[:1800])
