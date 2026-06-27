#!/usr/bin/env python3
"""Argus CLI — 로컬 머신에서 API 호출"""

import argparse
import json
import sys
from urllib.parse import urljoin

import httpx

DEFAULT_BASE_URL = "http://192.168.0.113:8000"
TIMEOUT = 30.0


def pprint(data: dict) -> None:
    """Pretty print JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def handle_error(resp: httpx.Response) -> None:
    """HTTP 에러 처리"""
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"[ERROR] HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)


def cmd_search(args: argparse.Namespace) -> None:
    """검색 서브커맨드"""
    payload = {
        "query": args.query,
        "max_results": args.max_results,
        "include_answer": args.include_answer,
        "search_depth": args.depth,
        "include_raw_content": args.include_raw,
    }

    if args.time_range:
        payload["time_range"] = args.time_range

    url = urljoin(args.url, "/v1/search")
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(url, json=payload)
        handle_error(resp)
        data = resp.json()

    if args.raw:
        pprint(data)
        return

    print(f"🔍 Query: {data['query']}")
    print(f"⏱️  Response time: {data['response_time']}s")
    print()

    if data.get("answer"):
        print("💡 AI Answer:")
        print(data["answer"])
        print()

    print(f"📄 Results ({len(data['results'])}):")
    for i, r in enumerate(data["results"], 1):
        print(f"  {i}. [{r['score']:.2f}] {r['title']}")
        print(f"     {r['url']}")
        snippet = r['content'][:200].replace('\n', ' ')
        print(f"     {snippet}...")
        print()


def cmd_extract(args: argparse.Namespace) -> None:
    """URL 추출 서브커맨드"""
    payload = {
        "urls": args.urls,
        "extract_depth": args.depth,
        "include_images": args.include_images,
    }

    url = urljoin(args.url, "/v1/extract")
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(url, json=payload)
        handle_error(resp)
        data = resp.json()

    if args.raw:
        pprint(data)
        return

    print(f"⏱️  Response time: {data['response_time']}s")
    print()

    for r in data["results"]:
        print(f"📄 {r['url']}")
        if r.get("title"):
            print(f"   Title: {r['title']}")
        if r.get("author"):
            print(f"   Author: {r['author']}")
        content = r['raw_content'][:300].replace('\n', ' ')
        print(f"   Content: {content}...")
        print()

    if data.get("failed_results"):
        print(f"⚠️  Failed URLs: {data['failed_results']}")


def cmd_answer(args: argparse.Namespace) -> None:
    """Q&A 서브커맨드"""
    payload = {
        "query": args.query,
        "max_results": args.max_results,
        "include_sources": not args.no_sources,
        "search_depth": args.depth,
    }

    url = urljoin(args.url, "/v1/answer")
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(url, json=payload)
        handle_error(resp)
        data = resp.json()

    if args.raw:
        pprint(data)
        return

    print(f"❓ Question: {data['query']}")
    print(f"⏱️  Response time: {data['response_time']}s")
    print()
    print("💡 Answer:")
    print(data["answer"])
    print()

    if data.get("sources"):
        print("📚 Sources:")
        for i, s in enumerate(data["sources"], 1):
            print(f"  {i}. [{s['score']:.2f}] {s['title']} — {s['url']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="argus",
        description="Argus CLI — 맥미니(192.168.0.113) 웹검색/추출/Q&A 호출"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"API Base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="원본 JSON 출력 (pretty print)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # search
    search_parser = subparsers.add_parser("search", help="웹 검색")
    search_parser.add_argument("query", help="검색어")
    search_parser.add_argument("-n", "--max-results", type=int, default=5)
    search_parser.add_argument("--answer", action="store_true", dest="include_answer")
    search_parser.add_argument("--depth", choices=["basic", "advanced"], default="advanced")
    search_parser.add_argument("--include-raw", action="store_true")
    search_parser.add_argument("--time-range", choices=["day", "week", "month", "year"])
    search_parser.set_defaults(func=cmd_search)

    # extract
    extract_parser = subparsers.add_parser("extract", help="URL에서 콘텐츠 추출")
    extract_parser.add_argument("urls", nargs="+", help="추출할 URL 목록")
    extract_parser.add_argument("--depth", choices=["basic", "advanced"], default="advanced")
    extract_parser.add_argument("--include-images", action="store_true")
    extract_parser.set_defaults(func=cmd_extract)

    # answer
    answer_parser = subparsers.add_parser("answer", help="검색 기반 Q&A")
    answer_parser.add_argument("query", help="질문")
    answer_parser.add_argument("-n", "--max-results", type=int, default=5)
    answer_parser.add_argument("--depth", choices=["basic", "advanced"], default="advanced")
    answer_parser.add_argument("--no-sources", action="store_true", help="출처 제외")
    answer_parser.set_defaults(func=cmd_answer)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
