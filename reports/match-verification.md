# RQ1 — match verification sheet (census, all 8 matches)

Seed 20260831. **Every** match from the three 30-PR arms, not a sample: the
population is 8, so there is no sampling error to carry.

**Blind twice over.** The judge's verdict and reason are not shown, and neither
is the arm — ids are `M1`..`M8` in shuffled order. Both are joined afterwards
from `work/match/match_sheet_key.json`.

Below is **exactly what `match_v1` saw**: two comments and their lines, nothing
else. No code. That is deliberate — judging the judge on evidence it never had
would measure your extra information, not its accuracy.

## Pass 1 — record in `verdict_comments_only`

`equivalent` / `not_equivalent`. The frozen rubric is `prompts/match_v1.md`;
it is binary and explicit that **uncertain means `not_equivalent`** — under-match
rather than over-match, because a false `equivalent` inflates recall and that is
the one error this evaluation must not make. Put hedges in `notes`, not in the
verdict.

## Pass 2 — only after pass 1 is complete for all 8

Open `match-verification-chunks.md`, which shows the diff chunk the reviewer saw
for each id, and record `verdict_with_code`. This answers a different question —
*is the match real* — and the gap between the two columns is itself a result.

---

## M1

**File:** `src/main/java/org/mockito/plugins/MockitoPlugins.java`  •  human on line 58, model on line 58 (Δ 0)  •  [PR #3129](https://github.com/mockito/mockito/pull/3129#discussion_r1346925228)

**Human reviewer comment:**

> This interface can be implemented, meaning that we can break downstream projects. We should add a default implementation and probably also mark this interface with `@NotExtensible`

**Model reviewer comment:**

> Adding an abstract method to this published interface is a source- and binary-incompatible change for anyone who implements `MockitoPlugins` themselves. Consider giving it a `default` implementation (e.g. throwing `UnsupportedOperationException`) so existing implementors keep compiling.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---not_equivalent

## M2

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

---equivalent

## M3

**File:** `src/main/java/org/mockito/internal/debugging/LocationFactory.java`  •  human on line 26, model on line 27 (Δ 1)  •  [PR #2883](https://github.com/mockito/mockito/pull/2883#discussion_r1083402617)

**Human reviewer comment:**

> Nit: this whole factory can now be removed and we can use the relevant location directly

**Model reviewer comment:**

> Now that the factory is a single unconditional lambda, the `Factory` interface, the `factory` field and `createLocationFactory()` no longer buy anything: `create(boolean)` could just `return new LocationImpl(inline);` directly. Consider dropping the indirection along with the JDK-version branching.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---equivalent

## M4

**File:** `src/main/java/org/mockito/plugins/MockitoPlugins.java`  •  human on line 58, model on line 58 (Δ 0)  •  [PR #3129](https://github.com/mockito/mockito/pull/3129#discussion_r1346925228)

**Human reviewer comment:**

> This interface can be implemented, meaning that we can break downstream projects. We should add a default implementation and probably also mark this interface with `@NotExtensible`

**Model reviewer comment:**

> This adds a new abstract method to a public interface with no default implementation. If any external code implements MockitoPlugins directly, this is a breaking change for them — is that acceptable here, or should this get a default method for compatibility?

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---equivalent

## M5

**File:** `src/test/java/com/puppycrawl/tools/checkstyle/internal/XdocsExamplesAstConsistencyTest.java`  •  human on line 1159, model on line 1158 (Δ 1)  •  [PR #20604](https://github.com/checkstyle/checkstyle/pull/20604#discussion_r3554520938)

**Human reviewer comment:**

> pleas revert all unrelated to functional fix formatting changes.

**Model reviewer comment:**

> These lines are pure re-indentation of `containsMultipleExamples`, which this PR otherwise does not change. Unrelated formatting churn inflates the diff; consider leaving untouched methods alone.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---equivalent

## M6

**File:** `junit-platform-launcher/src/main/java/org/junit/platform/launcher/TestIdentifier.java`  •  human on line 47, model on line 45 (Δ 2)  •  [PR #4913](https://github.com/junit-team/junit-framework/pull/4913#discussion_r2329301541)

**Human reviewer comment:**

> This is no longer the case. Please remove this comment and convert `/* final */` to `final` on all fields.
> 
> ```suggestion
> 	private final UniqueId uniqueId;
> ```

**Model reviewer comment:**

> Now that late initialization during deserialization is gone, the comment "effectively final but not technically due to late initialization when deserializing" no longer holds; these fields can be declared `final` and the `/* final */` markers dropped.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---equivalent

## M7

**File:** `src/main/java/com/puppycrawl/tools/checkstyle/checks/javadoc/JavadocTypeCheck.java`  •  human on line 421, model on line 421 (Δ 0)  •  [PR #20351](https://github.com/checkstyle/checkstyle/pull/20351#discussion_r3464406084)

**Human reviewer comment:**

> Can you refer to https://github.com/checkstyle/checkstyle/pull/19809#discussion_r3240257202 ? The Apostrophe thing does work, but why not just fix it from the violation message itself? Even this has `+ SPACE` which is hacky.

**Model reviewer comment:**

> The quoting is assembled at the call site by concatenating APOSTROPHE around the argument. Putting the quotes in the MSG_MISSING_TAG message property instead (as ''{0}'' in the properties file) would keep the formatting with the message text and avoid growing this concatenation chain further.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---equivalent

## M8

**File:** `junit-jupiter-migrationsupport/src/main/java/org/junit/jupiter/migrationsupport/EnableJUnit4MigrationSupport.java`  •  human on line 53, model on line 55 (Δ 2)  •  [PR #4609](https://github.com/junit-team/junit-framework/pull/4609#discussion_r2121172243)

**Human reviewer comment:**

> Missing `@deprecated` Javadoc tag

**Model reviewer comment:**

> The annotation is now @Deprecated(forRemoval = true) but the Javadoc above has no @deprecated tag. For a public API marked for removal, add a @deprecated paragraph naming the replacement (e.g. Jupiter's @Disabled and the native extension model) so the compiler warning points users somewhere.

**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`

---equivalent
