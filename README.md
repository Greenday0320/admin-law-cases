# 대법원 행정법 판례 모음

스터디 그룹(5인 이내) 공유용으로 만든 정적 사이트. 국가법령정보센터 Open API로 대법원 행정판례를 수집해서 GitHub Pages로 배포한다.

- 사이트: https://greenday0320.github.io/admin-law-cases/
- 레포: https://github.com/Greenday0320/admin-law-cases (public — Pages가 무료 플랜에서 private 저장소를 지원하지 않아서 public으로 전환함. 판례 자체가 공공데이터라 노출 문제는 없음)

## 파일 구조

```
admin-law-cases/
├── index.html            # 목록 페이지 (data/cases.json을 fetch해서 렌더링)
├── data/cases.json        # 수집된 판례 데이터 (git에 커밋됨)
├── scripts/fetch_cases.py # 국가법령정보센터 API에서 판례 수집하는 스크립트
├── config.local.json      # OC 인증키 저장 (git 제외 대상, .gitignore에 등록됨)
└── .gitignore
```

## 데이터 파이프라인

국가법령정보센터 Open API (https://open.law.go.kr) 사용. OC 인증키는 `config.local.json`에 로컬로만 저장(절대 커밋 안 됨).

**목록 조회**: `http://www.law.go.kr/DRF/lawSearch.do?target=prec&type=JSON`
- `org=400201` — 법원종류: 대법원
- `datSrcNm=대법원` — **반드시 필요**. 이게 없으면 국세법령정보시스템 등 미러링된 데이터가 섞여 들어오고, 그 판례일련번호로는 본문 조회가 실패함
- `prncYd=20260101~{오늘}` — 2026년 이후 선고 판례만
- `sort=ddes` — 최신순
- `display=100&page=N` — 페이지네이션

**본문 조회**: `http://www.law.go.kr/DRF/lawService.do?target=prec&ID={판례일련번호}&type=JSON`
- 판시사항/판결요지/참조조문/참조판례/판례내용 반환

**필터링 (스크립트 내부에서 처리, API 자체 필터 아님)**:
1. `사건종류명`에 "행정" 포함 (예: "일반행정")
2. `사건번호`에 "두" 포함 — 대법원 상고심 행정사건의 사건부호. "수"(재심), "허"(특허) 등은 제외

## 새 판례 추가하는 법

```bash
cd admin-law-cases
python scripts/fetch_cases.py   # 이미 있는 건 건너뛰고 새 판례만 추가
git add data/cases.json
git commit -m "add new cases"
git push   # push하면 GitHub Pages 자동 재배포
```

`index.html`의 `최근 업데이트: YYYY-MM-DD` 줄은 **수동으로 갱신**해야 함 (자동화 안 되어 있음).

## 디자인

`c:\Users\82103\Desktop\교육부위키\` 프로젝트의 CSS 디자인 시스템을 참고해서 이식함:
- CSS 커스텀 프로퍼티로 라이트/다크 테마 지원 (`prefers-color-scheme`)
- accent 컬러 `#3652d9` (다크모드 `#93a6ff`)
- 카드형 리스트(`doc-card-list`/`doc-card`) + 상단 안내 박스(`site-notice`) 패턴

## 알아둘 것

- **git 로컬 identity**: 이 저장소에만 `user.email`/`user.name` 로컬 설정되어 있음 (전역 설정 아님)
- **브라우저 캐시**: GitHub Pages가 `Cache-Control: max-age=600`이라, 배포 직후 안 바뀐 것처럼 보이면 Ctrl+Shift+R로 강력 새로고침
- **로컬 미리보기**: `index.html`에 판례 데이터가 직접 임베드되어 있어서(fetch 안 씀), 폴더에서 더블클릭해서 `file://`로 열어도 정상 작동함. `scripts/fetch_cases.py`를 실행할 때마다 `data/cases.json`을 갱신하고, 그 내용을 `index.html` 안의 `<script id="cases-data">` 블록에도 자동으로 다시 채워 넣음

## 다음에 할 수 있는 것

- 검색/필터/태그 기능 (지금은 단순 목록 단계)
- GitHub Actions로 수집 스크립트 주기 자동 실행
