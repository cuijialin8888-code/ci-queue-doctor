import json
import unittest
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from ci_queue_doctor.github import GitHubApiError, GitHubClient


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class JobPaginationTests(unittest.TestCase):
    def test_jobs_after_first_page_are_preserved_in_order(self):
        expected = [{"id": index, "status": "completed"} for index in range(205)]
        expected[-1]["status"] = "queued"
        seen = []

        def opener(request, timeout):
            self.assertEqual(request.method, "GET")
            self.assertEqual(urlsplit(request.full_url).path, "/repos/a/b/actions/runs/123/jobs")
            query = parse_qs(urlsplit(request.full_url).query)
            self.assertEqual(query["per_page"], ["100"])
            page = int(query.get("page", ["1"])[0])
            seen.append(page)
            batch = expected[(page - 1) * 100:page * 100]
            return Response({"total_count": 205, "jobs": batch})

        self.assertEqual(GitHubClient(opener=opener).list_jobs("a/b", 123), expected)
        self.assertEqual(seen, [1, 2, 3])

    def test_single_page_does_not_make_extra_requests(self):
        seen = []

        def opener(request, timeout):
            seen.append(request.full_url)
            return Response({"total_count": 1, "jobs": [{"id": 1}]})

        self.assertEqual(GitHubClient(opener=opener).list_jobs("a/b", 1), [{"id": 1}])
        self.assertEqual(len(seen), 1)

    def test_missing_count_uses_page_length(self):
        seen = []

        def opener(request, timeout):
            seen.append(request.full_url)
            batch = [{"id": index} for index in range(100)] if len(seen) == 1 else []
            return Response({"jobs": batch})

        self.assertEqual(len(GitHubClient(opener=opener).list_jobs("a/b", 1)), 100)
        self.assertEqual(len(seen), 2)

    def test_incomplete_or_malformed_pages_are_errors(self):
        for second in ({"total_count": 101, "jobs": []}, {"jobs": None}):
            with self.subTest(second=second):
                seen = []

                def opener(request, timeout, payload=second, calls=seen):
                    calls.append(request.full_url)
                    if len(calls) == 1:
                        return Response({"total_count": 101, "jobs": [{}] * 100})
                    return Response(payload)

                with self.assertRaises(GitHubApiError):
                    GitHubClient(opener=opener).list_jobs("a/b", 1)

    def test_later_page_http_error_does_not_return_partial_jobs(self):
        seen = []

        def opener(request, timeout):
            seen.append(request.full_url)
            if len(seen) > 1:
                raise HTTPError(request.full_url, 403, "Forbidden", {}, None)
            return Response({"total_count": 101, "jobs": [{}] * 100})

        with self.assertRaisesRegex(GitHubApiError, "403"):
            GitHubClient(opener=opener).list_jobs("a/b", 1)

    def test_pagination_is_bounded(self):
        seen = []

        def opener(request, timeout):
            seen.append(request.full_url)
            return Response({"jobs": [{}] * 100})

        with self.assertRaisesRegex(GitHubApiError, "pagination limit"):
            GitHubClient(opener=opener).list_jobs("a/b", 1)
        self.assertEqual(len(seen), 100)
