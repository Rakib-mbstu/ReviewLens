# RQ1 — match verification sheet (census, all 5 matches)

Seed 20260904. **Every** match from the 87-PR full-corpus qwen run, not a sample: the
population is 5, so there is no sampling error to carry.

**Blind to the judge.** Its verdict and reason are not shown, and the ids are
`M1`..`M5` in shuffled order. This is a single run, so there is no arm to
hide; the judge's own output is joined afterwards from `work/match/match_full87_key.json`.

Below is **exactly what `match_v1` saw**: two comments and their lines, nothing
else. No code. That is deliberate — judging the judge on evidence it never had
would measure your extra information, not its accuracy.

## Pass 1 — record in `verdict_comments_only`

`equivalent` / `not_equivalent`. The frozen rubric is `prompts/match_v1.md`;
it is binary and explicit that **uncertain means `not_equivalent`** — under-match
rather than over-match, because a false `equivalent` inflates recall and that is
the one error this evaluation must not make. Put hedges in `notes`, not in the
verdict.

## Pass 2 — only after pass 1 is complete for all 5

Open `match-verification-full87-chunks.md`, which shows the diff chunk the reviewer saw
for each id, and record `verdict_with_code`. This answers a different question —
*is the match real* — and the gap between the two columns is itself a result.

---

## M1

**File:** `mockito-core/src/main/java/org/mockito/internal/stubbing/InvocationContainerImpl.java`  •  human on line 88, model on line 86 (Δ 2)  •  [PR #3506](https://github.com/mockito/mockito/pull/3506#discussion_r1869558645)

**Human reviewer comment:**

> Instead of throw a NPE here, let's use `MockitoException` instead and provide a more descriptive error message:
> 
> ```java
> throw new MockitoException("Unable to find answer for " + invocation + ". Did you configure a stubbing for this method?");
> ```

**Model reviewer comment:**

> Potential NullPointerException if findAnswerFor returns null. The null check is good, but the error message could be more informative about why no answer was found.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---

## M2

**File:** `junit-platform-console/src/main/java/org/junit/platform/console/output/VerboseTreePrintingListener.java`  •  human on line 177, model on line 177 (Δ 0)  •  [PR #5930](https://github.com/junit-team/junit-framework/pull/5930#discussion_r3682273475)

**Human reviewer comment:**

> While it is likely that the root of a test plan is also a test identifier without a parent, it would be more accurate for the loop condition to halt when current node has no parent.
> 
> Typically this would be written like this:
> 
> ```
> while ((parent = testPlan.getParent().orElse(null)) != null) {
> ```

**Model reviewer comment:**

> The loop condition in nestingLevel could be simplified. Instead of checking for roots and then getting parent, we could directly check if parent exists and iterate until we reach a root.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---

## M3

**File:** `src/test/java/org/mockitousage/strictness/StrictnessMockAnnotationTest.java`  •  human on line 39, model on line 38 (Δ 1)  •  [PR #2650](https://github.com/mockito/mockito/pull/2650#discussion_r882658824)

**Human reviewer comment:**

> Nit: I think we can use a lambda here, can we not?
> 
> ```java
> () -> ProductionCode.simpleMethod(regularMock, "4")
> ```

**Model reviewer comment:**

> The test uses an anonymous inner class for ThrowableAssert.ThrowingCallable. Consider using a lambda expression for better readability.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---

## M4

**File:** `platform-tests/src/test/java/org/junit/platform/reporting/open/xml/OpenTestReportGeneratingListenerTests.java`  •  human on line 353, model on line 352 (Δ 1)  •  [PR #5096](https://github.com/junit-team/junit-framework/pull/5096#discussion_r2465389749)

**Human reviewer comment:**

> When is this needed? Can't we just rethrow the exception?
> 
> ```suggestion
> 					fail(e);
> ```

**Model reviewer comment:**

> RuntimeException is thrown in the server thread but not properly propagated to the test, which could lead to silent failures. The test should fail if the server thread encounters an exception.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---

## M5

**File:** `junit-jupiter-api/src/main/java/org/junit/jupiter/api/ClassOrderer.java`  •  human on line 58, model on line 56 (Δ 2)  •  [PR #4842](https://github.com/junit-team/junit-framework/pull/4842#discussion_r2285495961)

**Human reviewer comment:**

> I would simply list `Default` along with the other implementations in the above list, since the Javadoc for `Default` explains its purpose.
> 
> Plus, we don't explain the purpose of any of the other implementations in the class-level Javadoc.

**Model reviewer comment:**

> The new Default class is mentioned in the documentation but not shown in the built-in implementations list. Consider adding it to the list for consistency.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---
