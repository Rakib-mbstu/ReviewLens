# Zenodo — deferred, with everything needed to finish it

**Status: not done.** Parked 2026-09-04 after the GitHub authorization step did
not go through. Nothing in the repo depends on this; it is the last item on the
pre-outreach list (T23) and it is polish, not a blocker. The repo already has a
working link, green CI, the technical report, a recorded demo, a LICENSE, pinned
dependencies, and a `CITATION.cff` that renders GitHub's **Cite this
repository** button today.

## What a DOI actually buys

1. **An immutable snapshot.** The main reason. The backlog still holds
   "run the Claude arms over the full corpus" and "add a second rater", so this
   repo may move. If an application says *1.6% recall, 5/5 human-verified*, the
   reader should see that state, not whatever `main` looks like months later.
2. **It survives a rename, a deletion, or a changed username.** GitHub URLs do
   not.
3. **It reads as a research output** in a CV or statement of purpose.

It buys **no peer review and no validation**. A DOI is a permalink with good
manners.

## Why it stalled, and why that is probably not a real blocker

The account belongs to one organization, `DSInnovators`, which has third-party
OAuth app restrictions enabled. On GitHub's authorize screen a restricted org
shows a red ✗ with a "Request access" button, which reads as a hard stop.

It is not one for this repo. `Rakib-mbstu/ReviewLens` is a **personal** repo
(`isInOrganization: false`, checked 2026-09-04) — the restriction is scoped to
the org's own repos. Clicking **Authorize zenodo** at the bottom of that screen
should still work, and personal repos sync. If Zenodo's repo list comes up empty
afterwards, press **Sync now** on that page; that is usually a stale cache
rather than a permissions failure.

If it genuinely refuses — some orgs enforce SAML SSO that poisons the whole
grant — use the manual path below. It needs no GitHub authorization at all.

## The manual path is the better one here anyway

Zenodo's GitHub integration archives **only the repo tarball**. It does not pull
in release assets, so the artifact bundle — the mined corpus, the run outputs
with raw request/response bytes, and the response cache — would be missing, and
the archived copy would be the one that *cannot* replay the study. Uploading by
hand fixes that.

The cost of going manual: no automatic minting on future releases; repeat this
by hand. For a feature-frozen project shipping its final state, that is not a
real cost.

## Rebuilding the two upload files

They were built once into a temporary directory and are not committed — both
regenerate exactly:

```bash
# 1. the source at the v0.1.1 tag
git archive --format=tar.gz --prefix=ReviewLens-0.1.1/ \
    -o ReviewLens-0.1.1-source.tar.gz v0.1.1

# 2. the evaluation artifacts, from the v0.1.0 release
gh release download v0.1.0 --repo Rakib-mbstu/ReviewLens --clobber

shasum -a 256 *.tar.gz
```

Expected, and verified 2026-09-04:

| file | size | sha256 |
|---|---|---|
| `ReviewLens-0.1.1-source.tar.gz` | 6.5 MB | `3e86ab33eb17476509a115f989ab3d0aa8b0f41e529bf768cb4f3df7bbef6bd5` |
| `reviewlens-artifacts-v0.1.0.tar.gz` | 3.1 MB | `6803efe5d3f8c4a6bb5f6289f66be55d1dae26fc30de85e5e090749e6ca85b26` |

The artifacts hash is the one `work/demo/fetch_artifacts.sh` already pins, so
the archived copy is byte-identical to what the demo verifies against.

⚠️ The source tarball's hash depends on the tag. If `v0.1.1` is ever re-cut, it
changes; the artifacts hash must not change, because that URL is baked into
`fetch_artifacts.sh`.

## Deposition fields

```
Upload type:       Software
Title:             ReviewLens: an LLM Java code reviewer, and a human check on the judges that score it
Authors:           Islam, Mir Rakibul        <- verify this split; it sets every citation
Publication date:  2026-09-04
Version:           0.1.1
Language:          English
License:           MIT License
Keywords:          ai4se; empirical software engineering; code review; LLM-as-a-judge;
                   LLM evaluation; reproducible research; Java
Related identifiers:
  https://github.com/Rakib-mbstu/ReviewLens              relation: is supplement to
  https://github.com/Rakib-mbstu/ReviewLens/tree/v0.1.1  relation: is identical to
```

### Description

> ReviewLens is an LLM-based Java pull request reviewer and an empirical study
> of its own evaluation. It reviews merged pull requests from JUnit 5, Mockito
> and Checkstyle at their pre-review state and measures recall against the
> review comments real maintainers left on them: 328 comments across 90 pull
> requests.
>
> Recall for the one model run over the full corpus is 1.6% (5 of 318 human
> comments on the 87 pull requests it covered). All five of those matches were
> verified by a human.
>
> Two frozen LLM judges score this pipeline, and both were checked against a
> human rater. The matcher held: 12 of 13 verdicts upheld across two censuses.
> The hallucination screen did not: it agreed with the human at chance level
> (Cohen's kappa = 0.046), and its decisive per-arm result is retracted rather
> than caveated. That contrast is the study's primary finding. A frozen,
> deterministic, rubric-driven judge is not thereby a correct one, and only the
> human check told the two judges apart.
>
> A three-model comparison on a 30-PR subset gives 1.0%, 1.0% and 4.9% recall
> after human verification; the differences are not significant at this sample
> size (Fisher exact p = 0.212) and no ordering is claimed.
>
> The archive contains the full source, the frozen prompts with their freeze
> dates and hashes, every evaluation report, the human verification sheets and
> verdicts, and a separate artifact bundle holding the mined corpus, all run
> outputs with raw request and response bytes, and the LLM response cache. The
> evaluation replays offline from that cache at zero cost and without an API
> key.

## Order of operations

1. **If using the GitHub integration:** enable Zenodo's switch for the repo
   **before** publishing a GitHub Release. Zenodo only captures releases
   published *after* the switch is on — publish first and the DOI silently does
   not mint.
2. `v0.1.1` is **tagged but has no GitHub Release**, deliberately, so that
   ordering is still open.
3. **Never retag `v0.1.0`.** Its asset URL is baked into
   `work/demo/fetch_artifacts.sh`.
4. After minting: uncomment the `identifiers:` block at the bottom of
   `CITATION.cff` and paste the real DOI.

## Also check before minting

The author name split in `CITATION.cff` — `given-names: "Mir Rakibul"` /
`family-names: "Islam"` — is the common rendering but was not confirmed. It
decides how every citation formats, and a DOI minted against the wrong split is
awkward to correct. `orcid:` and `email:` were left out rather than guessed.

## If you would rather not

Software Heritage archives a public repo with no authorization at all — you
submit the URL and it crawls. It gives a SWHID rather than a DOI, so it is
permanence without the citable identifier. A reasonable fallback if Zenodo stays
blocked and the archival guarantee is what you actually wanted.
