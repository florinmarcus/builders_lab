-- An "evals" firm for eval runs (26 Nov 2026, parking lot S161). It holds no firm data. Its key is used only by
-- answer evals against the regulations server, so their tool calls, traces and daily quota stay apart from the
-- demo firm's (500 tool calls a day). A full answer run is about 500 searches; the baseline needs three.
insert into firms (slug, name) values ('evals', 'Evals (no firm data)') on conflict (slug) do nothing;

insert into quota_limits (firm_id, metric, daily_limit)
select id, 'tool_calls', 5000 from firms where slug = 'evals'
on conflict (firm_id, metric) do nothing;
