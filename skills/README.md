# App tips ("skills")

Optional, off by default (`"use_skills": true` in a config turns it on).

A file `skills/<key>.md` is added to the prompt under `APP TIPS` only while an
app whose package name contains `<key>` is in the foreground. Example:
`markor.md` applies to `net.gsantner.markor`, `smsmessenger.md` applies to
`com.simplemobiletools.smsmessenger`.

This is progressive disclosure (Day 2 / Day 3): the tips cost tokens only when
they are relevant, and the stable system prompt stays untouched.

Use it for a fix that is "a judgement you can state in one clear sentence"
(Day 5: put the fix in *Instructions*). Keep each file to a few short lines.
Write tips only after you have seen the failure in a recording, and re-run the
evaluation afterwards: a tip is a change to the agent like any other.

This folder ships without tips on purpose, and the three shipped configs
(v1, v2, v3) do not use it. If you add tips, do it in a new config (for
example `v4_skills.json`) so the earlier results stay comparable.
