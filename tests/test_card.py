import unittest

from grudges import card, run


def rec(task, model, status):
    return {"task": task, "agent": "codex", "model": model, "status": status,
            "seconds": 10, "output_tokens": 1, "cost_usd": None}


class CardTest(unittest.TestCase):
    def test_counts_titles_and_escaping(self):
        records = [rec("a", "m1", "solved"), rec("a", "m1", "solved"), rec("b", "m1", "failed"),
                   rec("a", "m2", "failed"), rec("b", "m2", "provider_error")]
        result = {"run_id": "r", "agent": "codex", "attempts": 2, "summary": run.summarize(records)}
        out = card.render(result, {"a": "<script>x</script> title"})
        self.assertIn("<b>2/3</b> solved/scored", out)
        self.assertIn("1 of 2 majority-fixed tasks", out)
        self.assertIn("2 tasks my coding agent failed", out)
        self.assertIn("1 error · 2 missing", out)
        self.assertNotIn("<script>x", out)
        self.assertIn("&lt;script&gt;x&lt;/script&gt; title", out)
        self.assertIn("m1<small>in Codex</small>", out)


    def test_pack_runs_do_not_claim_personal_failures(self):
        records = [rec("a", "m1", "solved"), rec("b", "m1", "failed")]
        result = {"run_id": "r", "agent": "codex", "attempts": 1, "summary": run.summarize(records),
                  "source": "pack:starter"}
        out = card.render(result)
        self.assertNotIn("my coding agent failed", out)
        self.assertIn("2 tasks from the starter pack", out)


    def test_cost_and_time_shown_and_ties_ranked_by_cost(self):
        records = [dict(rec("a", "pricey", "solved"), cost_usd=7.0, seconds=300),
                   dict(rec("a", "cheap", "solved"), cost_usd=0.1, seconds=120)]
        out = card.render({"run_id": "r", "agent": "codex", "attempts": 1, "summary": run.summarize(records)})
        self.assertIn("$0.10", out)
        self.assertIn("$7.00", out)
        self.assertIn("2 min median", out)
        self.assertLess(out.index("cheap<small>"), out.index("pricey<small>"))

    def test_rules_runs_pair_each_model_without_then_with_rules(self):
        records = [dict(rec("a", "m1", "failed"), setup="without rules"),
                   dict(rec("a", "m1", "solved"), setup="with rules"),
                   dict(rec("a", "m0", "solved"), setup="with rules")]
        result = {"run_id": "r", "agent": "codex", "attempts": 1, "rules": True,
                  "summary": run.summarize(records)}
        out = card.render(result)
        self.assertIn("Do my rules improve results?", out)
        self.assertIn("m1<small>in Codex, without rules</small>", out)
        self.assertLess(out.index("m0<small>"), out.index("m1<small>in Codex, without"))
        self.assertLess(out.index("m1<small>in Codex, without"), out.index("m1<small>in Codex, with rules"))

    def test_attempt_evidence_and_incomplete_tasks(self):
        records = [rec("a", "m", status) for status in
                   ["solved", "failed", "timeout", "provider_error"]]
        records += [rec("b", "other", "solved")]
        out = card.render({"attempts": 5, "summary": run.summarize(records)})
        self.assertIn("<b>1/3</b> solved/scored", out)
        self.assertIn("1 error · 6 missing", out)
        self.assertIn("<strong>1/3 solved/scored</strong><small>1 error · 1 missing", out)
        self.assertIn("0/0 solved/scored</strong><small>0 errors · 5 missing · no scored attempts", out)
        self.assertIn("0 of 2 majority-fixed tasks", out)
        self.assertIn("all planned attempts scored and more than half solved", out)
        self.assertIn("customer-data leak", out)

    def test_all_errors_and_empty_run_are_not_successes(self):
        records = [rec("a", "m", status) for status in
                   ["provider_error", "infra_error", "grader_error"]]
        out = card.render({"attempts": 3, "summary": run.summarize(records)})
        self.assertIn("<b>0/0</b> solved/scored", out)
        self.assertIn("3 errors · 0 missing · no scored attempts", out)
        self.assertIn("0 of 1 majority-fixed tasks", out)
        self.assertIn("cost unavailable", out)
        empty = card.render({"attempts": 3, "summary": {}, "tasks": ["/private/task"]})
        self.assertIn("No attempts reported", empty)
        self.assertNotIn("/private/task", empty)

    def test_zero_cost_is_known_and_ranks_before_missing_cost(self):
        summary = run.summarize([rec("a", m, "solved") for m in ["free", "unknown", "paid"]])
        summary["codex · free"]["cost_usd"] = 0
        summary["codex · paid"]["cost_usd"] = .1
        del summary["codex · unknown"]["cost_usd"]
        out = card.render({"attempts": 1, "summary": summary})
        self.assertIn("$0.00", out)
        self.assertIn("cost unavailable", out)
        self.assertLess(out.index("free<small>"), out.index("paid<small>"))
        self.assertLess(out.index("paid<small>"), out.index("unknown<small>"))

    def test_both_baseline_labels_sort_before_rules(self):
        for baseline in ["as captured", "without rules"]:
            with self.subTest(baseline=baseline):
                summary = run.summarize([dict(rec("a", "m", "solved"), setup=setup)
                                         for setup in ["with rules", baseline]])
                out = card.render({"attempts": 1, "rules": True, "summary": summary})
                self.assertLess(out.index(f"in Codex, {baseline}"), out.index("in Codex, with rules"))

    def test_private_fields_and_unknown_status_are_not_exported(self):
        private = "/private/customer/prompt.txt"
        summary = run.summarize([rec(private, '<script>model</script>', private)])
        result = {"attempts": 1, "summary": summary, "run_id": private,
                  "agent": private, "records": [{"prompt": "SECRET PROMPT"}],
                  "tasks": [private], "source": "pack:" + private}
        out = card.render(result)
        self.assertNotIn(private, out)
        self.assertNotIn("SECRET PROMPT", out)
        self.assertNotIn("<script>", out)
        self.assertIn("Task 1", out)
        self.assertIn("&lt;script&gt;model&lt;/script&gt;", out)
        out = card.render(result, {private: 'Reviewed <title> & "quoted"'})
        self.assertIn("Reviewed &lt;title&gt; &amp; &quot;quoted&quot;", out)

    def test_majority_requires_complete_scoring_and_is_secondary(self):
        records = [rec("tie", "m", s) for s in ["solved", "failed"]]
        records += [rec("majority", "m", s) for s in ["solved", "provider_error"]]
        out = card.render({"attempts": 3, "summary": run.summarize(records)})
        self.assertIn("<b>2/3</b> solved/scored", out)
        self.assertIn("0 of 2 majority-fixed tasks", out)
        self.assertIn("all planned attempts scored", out)

    def test_extra_attempts_do_not_hide_an_unreported_task(self):
        summary = run.summarize([rec("a", "m", "solved") for _ in range(4)])
        out = card.render({"attempts": 2, "summary": summary,
                           "tasks": ["/private/a", "/private/b"]})
        self.assertIn("0 errors · 2 missing", out)
        self.assertIn("Task 2", out)
        self.assertIn("0/0 solved/scored</strong><small>0 errors · 2 missing", out)
        self.assertNotIn("/private/", out)

    def test_missing_placeholders_and_partial_cost(self):
        summary = run.summarize([rec("a", "m", s) for s in ["solved", "missing", "infra_error"]])
        summary["codex · m"].update(cost_usd=.25, cost_complete=False)
        out = card.render({"attempts": 3, "summary": summary})
        self.assertIn("1 error · 1 missing", out)
        self.assertIn("$0.25 known cost (partial)", out)
        self.assertIn("0 of 1 majority-fixed tasks", out)

    def test_social_and_expanded_layout(self):
        for count in [1, 4, 6, 7, 10]:
            summary = run.summarize([rec("a", f"model-{i}", "solved") for i in range(count)])
            out = card.render({"attempts": 1, "summary": summary})
            section = out.split('aria-label="Results card"')[0].rsplit('<section', 1)[1]
            self.assertEqual("expanded" in section, count > 6)
            self.assertEqual(out.count('<div class="row">'), count)
            self.assertIn("width:1200px; height:630px", out)
            self.assertNotIn("transform:scale", out)
            self.assertIn('class="table-scroll"', out)


if __name__ == "__main__":
    unittest.main()
