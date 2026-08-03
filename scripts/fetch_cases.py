import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.local.json"
DATA_PATH = ROOT / "data" / "cases.json"

LIST_URL = "http://www.law.go.kr/DRF/lawSearch.do"
DETAIL_URL = "http://www.law.go.kr/DRF/lawService.do"

START_DATE = "20260101"  # 수집 시작 기준일 (2026년 판례부터)


def load_oc():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return config["oc"]


def fetch_json(url, params):
    query = urllib.parse.urlencode(params, encoding="utf-8")
    with urllib.request.urlopen(f"{url}?{query}", timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_list_page(oc, page):
    end_date = date.today().strftime("%Y%m%d")
    return fetch_json(LIST_URL, {
        "OC": oc,
        "target": "prec",
        "type": "JSON",
        "org": "400201",
        "datSrcNm": "대법원",
        "prncYd": f"{START_DATE}~{end_date}",
        "sort": "ddes",
        "display": 100,
        "page": page,
    })


def fetch_detail(oc, case_id):
    return fetch_json(DETAIL_URL, {
        "OC": oc,
        "target": "prec",
        "type": "JSON",
        "ID": case_id,
    })


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def load_existing():
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return []


def main():
    oc = load_oc()
    existing = load_existing()
    seen_ids = {c["판례일련번호"] for c in existing}

    candidates = []
    page = 1
    while True:
        result = fetch_list_page(oc, page)
        search = result.get("PrecSearch", {})
        items = search.get("prec", [])
        if not items:
            break

        for item in items:
            if "행정" not in item.get("사건종류명", ""):
                continue
            if "두" not in item.get("사건번호", ""):
                continue
            if item["판례일련번호"] in seen_ids:
                continue
            candidates.append(item)

        total_cnt = int(search.get("totalCnt", 0))
        if page * 100 >= total_cnt:
            break
        page += 1
        time.sleep(0.3)

    print(f"신규 행정판례 후보 {len(candidates)}건, 본문 조회 시작")

    for item in candidates:
        case_id = item["판례일련번호"]
        detail = fetch_detail(oc, case_id).get("PrecService", {})
        record = {
            "판례일련번호": case_id,
            "사건번호": item["사건번호"],
            "사건명": item["사건명"],
            "선고일자": detail.get("선고일자", item.get("선고일자", "").replace(".", "")),
            "법원명": detail.get("법원명", "대법원"),
            "사건종류명": detail.get("사건종류명", item.get("사건종류명", "")),
            "판결유형": detail.get("판결유형", ""),
            "판시사항": strip_html(detail.get("판시사항")),
            "판결요지": strip_html(detail.get("판결요지")),
            "참조조문": strip_html(detail.get("참조조문")),
            "참조판례": strip_html(detail.get("참조판례")),
            "판례내용": strip_html(detail.get("판례내용")),
        }
        existing.append(record)
        seen_ids.add(case_id)
        print(f"  수집: {record['사건번호']} {record['사건명']}")
        time.sleep(0.3)

    existing.sort(key=lambda c: c["선고일자"], reverse=True)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"완료. 총 {len(existing)}건 저장됨 -> {DATA_PATH}")


if __name__ == "__main__":
    main()
