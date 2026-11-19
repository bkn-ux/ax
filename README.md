# AX 2027 로드맵 제안

AX(AI Transformation)를 추진하는 기업을 위한 2027년 로드맵·마일스톤 제안 페이지와 1분 설명 영상.
두 가지 관점으로 만들었다.

| 폴더 | 관점 | 열기 |
|---|---|---|
| `hr/` | 기업 HR(인사) | `hr/index.html` |
| `search-firm/` | 서치펌(헤드헌팅) | `search-firm/index.html` |

각 폴더에 HTML 페이지, 1분 영상(키네틱 타이포와 라인아트, 한국어 음성), EDA 스크립트와 데이터, 영상 생성 스크립트가 있다.

## 꼭 알아둘 점

- **EDA 데이터는 시뮬레이션(가상)** 이며 실제 시장·사내 통계가 아니다(seed 고정). 금액과 비율은 모두 가설이다.
- 20안의 5색 채점은 작성자(모델)의 자체 판단이다. 서치펌 버전 채택 5안은 독립 평가 에이전트 2회 평가에서도 합격선 9.5에 도달하지 못했다(`search-firm/5color_plan.md`, 페이지 08절 참고).
- 영상 음성은 Windows 기본 한국어 합성음(Microsoft Heami)이며, 발음과 품질은 직접 들어보고 판단해야 한다.
- 영상 재생은 `index.html`과 같은 폴더의 mp4를 참조하므로 로컬 서버(`python -m http.server`)로 열어야 페이지 안에서 재생된다.

## 재현

```bash
pip install pandas numpy pillow imageio-ffmpeg
cd hr && python eda_hr.py && python make_video_hr.py
```
