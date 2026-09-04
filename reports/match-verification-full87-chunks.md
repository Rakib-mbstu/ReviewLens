# RQ1 — match verification, pass 2 (the code)

**Do not open this until pass 1 is complete for all 5 ids.** The diff chunk
the reviewer saw, per sheet id, recovered from the raw request the review
engine sent. Record `verdict_with_code` in `reports/match-verification-full87.csv`.

---

## M1

**File:** `mockito-core/src/main/java/org/mockito/internal/stubbing/InvocationContainerImpl.java`  •  human on line 88, model on line 86

```diff
  73:                 stubbed.addFirst(
  74:                         new StubbedInvocationMatcher(
  75:                                 answer, invocationForStubbing, effectiveStrictness));
  76:             }
  77:             return stubbed.getFirst();
  78:         }
  79:     }
  80: 
  81:     public void addConsecutiveAnswer(Answer<?> answer) {
  82:         addAnswer(answer, true, null);
  83:     }
  84: 
  85:     Object answerTo(Invocation invocation) throws Throwable {
- :         return findAnswerFor(invocation).answer(invocation);
+ 86:         StubbedInvocationMatcher matcher = findAnswerFor(invocation);
+ 87:         if (matcher == null) {
+ 88:             throw new NullPointerException("No answer found for: " + invocation);
+ 89:         }
+ 90:         return matcher.answer(invocation);
  91:     }
  92: 
  93:     public StubbedInvocationMatcher findAnswerFor(Invocation invocation) {
  94:         synchronized (stubbed) {
  95:             for (StubbedInvocationMatcher s : stubbed) {
  96:                 if (s.matches(invocation)) {
  97:                     s.markStubUsed(invocation);
  98:                     // TODO we should mark stubbed at the point of stubbing, not at the point where
  99:                     // the stub is being used
  100:                     invocation.markStubbed(new StubInfoImpl(s));
  101:                     return s;
  102:                 }
  103:             }
```

**Human:**

> Instead of throw a NPE here, let's use `MockitoException` instead and provide a more descriptive error message:
> 
> ```java
> throw new MockitoException("Unable to find answer for " + invocation + ". Did you configure a stubbing for this method?");
> ```

**Model:**

> Potential NullPointerException if findAnswerFor returns null. The null check is good, but the error message could be more informative about why no answer was found.

---

## M2

**File:** `junit-platform-console/src/main/java/org/junit/platform/console/output/VerboseTreePrintingListener.java`  •  human on line 177, model on line 177

```diff
  1: /*
  2:  * Copyright 2015-2026 the original author or authors.
  3:  *
  4:  * All rights reserved. This program and the accompanying materials are
  5:  * made available under the terms of the Eclipse Public License v2.0 which
  6:  * accompanies this distribution and is available at
  7:  *
  8:  * https://www.eclipse.org/legal/epl-v20.html
  9:  */
  10: 
  11: package org.junit.platform.console.output;
  12: 
+ 13: import static java.util.Objects.requireNonNull;
  14: import static org.apiguardian.api.API.Status.INTERNAL;
  15: import static org.junit.platform.commons.util.ExceptionUtils.readStackTrace;
  16: import static org.junit.platform.console.output.Style.NONE;
  17: 
  18: import java.io.PrintWriter;
- : import java.util.ArrayDeque;
- : import java.util.Deque;
+ 19: import java.util.Map;
+ 20: import java.util.Optional;
+ 21: import java.util.concurrent.ConcurrentHashMap;
  22: 
  23: import org.apiguardian.api.API;
+ 24: import org.jspecify.annotations.Nullable;
  25: import org.junit.platform.engine.TestExecutionResult;
+ 26: import org.junit.platform.engine.UniqueId;
  27: import org.junit.platform.engine.reporting.FileEntry;
  28: import org.junit.platform.engine.reporting.ReportEntry;
  29: import org.junit.platform.launcher.TestIdentifier;
  30: import org.junit.platform.launcher.TestPlan;
  31: 
  32: /**
  33:  * @since 1.0
  34:  */
  35: @API(status = INTERNAL, since = "1.14")
  36: public class VerboseTreePrintingListener implements DetailsPrintingListener {
  37: 
  38: 	private final PrintWriter out;
  39: 	private final Theme theme;
  40: 	private final ColorPalette colorPalette;
- : 	private final Deque<Long> frames;
  41: 	private final String[] verticals;
- : 	private long executionStartedMillis;
+ 42: 	private final Map<UniqueId, Long> startedMillisByUniqueId = new ConcurrentHashMap<>();
+ 43: 
+ 44: 	private @Nullable TestPlan testPlan;
  45: 
  46: 	public VerboseTreePrintingListener(PrintWriter out, ColorPalette colorPalette, int maxContainerNestingLevel,
  47: 			Theme theme) {
  48: 		this.out = out;
  49: 		this.colorPalette = colorPalette;
  50: 		this.theme = theme;
  51: 
- : 		// create frame stack and push initial root frame
- : 		this.frames = new ArrayDeque<>();
- : 		this.frames.push(0L);
- : 
- : 		// create and populate vertical indentation lookup table
+ 52: 		// create and populate vertical indentation lookup table, indexed by nesting level
  53: 		this.verticals = new String[Math.max(10, maxContainerNestingLevel) + 1];
- : 		this.verticals[0] = ""; // no frame
- : 		this.verticals[1] = ""; // synthetic root "/" level
- : 		this.verticals[2] = ""; // "engine" level
- : 
- : 		for (int i = 3; i < verticals.length; i++) {
+ 54: 		this.verticals[0] = ""; // "engine" level
+ 55: 		for (int i = 1; i < verticals.length; i++) {
  56: 			verticals[i] = verticals[i - 1] + theme.vertical();
  57: 		}
  58: 	}
  59: 
  60: 	@Override
  61: 	public void testPlanExecutionStarted(TestPlan testPlan) {
- : 		frames.push(System.currentTimeMillis());
+ 62: 		this.testPlan = testPlan;
  63: 
+ 64: 		StringBuilder output = new StringBuilder();
  65: 		String prefix = "Test plan execution started. Number of static tests: ";
- : 		printNumberOfTests(testPlan, prefix);
- : 		printf(Style.CONTAINER, "%s%n", theme.root());
+ 66: 		appendNumberOfTests(output, testPlan, prefix);
+ 67: 		append(output, Style.CONTAINER, "%s%n", theme.root());
+ 68: 		print(output);
  69: 	}
  70: 
  71: 	@Override
  72: 	public void testPlanExecutionFinished(TestPlan testPlan) {
- : 		frames.pop();
- : 
- : 		printNumberOfTests(testPlan, "Test plan execution finished. Number of all tests: ");
+ 73: 		StringBuilder output = new StringBuilder();
+ 74: 		appendNumberOfTests(output, testPlan, "Test plan execution finished. Number of all tests: ");
+ 75: 		print(output);
  76: 	}
  77: 
- : 	private void printNumberOfTests(TestPlan testPlan, String prefix) {
+ 78: 	private void appendNumberOfTests(StringBuilder output, TestPlan testPlan, String prefix) {
  79: 		long tests = testPlan.countTestIdentifiers(TestIdentifier::isTest);
- : 		printf(NONE, "%s", prefix);
- : 		printf(Style.TEST, "%d%n", tests);
+ 80: 		append(output, NONE, "%s", prefix);
+ 81: 		append(output, Style.TEST, "%d%n", tests);
  82: 	}
  83: 
  84: 	@Override
  85: 	public void executionStarted(TestIdentifier testIdentifier) {
- : 		this.executionStartedMillis = System.currentTimeMillis();
+ 86: 		startedMillisByUniqueId.put(testIdentifier.getUniqueIdObject(), System.currentTimeMillis());
+ 87: 		int nestingLevel = nestingLevel(testIdentifier);
+ 88: 		StringBuilder output = new StringBuilder();
+ 89: 		appendVerticals(output, nestingLevel, theme.entry());
  90: 		if (testIdentifier.isContainer()) {
- : 			printVerticals(theme.entry());
- : 			printf(Style.CONTAINER, " %s", testIdentifier.getDisplayName());
- : 			printf(NONE, "%n");
- : 			frames.push(System.currentTimeMillis());
+ 91: 			append(output, Style.CONTAINER, " %s", testIdentifier.getDisplayName());
+ 92: 			append(output, NONE, "%n");
  93: 		}
- : 		if (testIdentifier.isContainer()) {
- : 			return;
+ 94: 		else {
+ 95: 			append(output, Style.valueOf(testIdentifier), " %s%n", testIdentifier.getDisplayName());
+ 96: 			appendDetails(output, nestingLevel, testIdentifier);
  97: 		}
- : 		printVerticals(theme.entry());
- : 		printf(Style.valueOf(testIdentifier), " %s%n", testIdentifier.getDisplayName());
- : 		printDetails(testIdentifier);
+ 98: 		print(output);
  99: 	}
  100: 
  101: 	@Override
  102: 	public void executionFinished(TestIdentifier testIdentifier, TestExecutionResult testExecutionResult) {
- : 		testExecutionResult.getThrowable().ifPresent(t -> printDetail(Style.FAILED, "caught", readStackTrace(t)));
+ 103: 		long startedMillis = requireNonNull(startedMillisByUniqueId.remove(testIdentifier.getUniqueIdObject()));
+ 104: 		int nestingLevel = nestingLevel(testIdentifier);
+ 105: 		StringBuilder output = new StringBuilder();
+ 106: 		testExecutionResult.getThrowable().ifPresent(
+ 107: 			t -> appendDetail(output, nestingLevel, Style.FAILED, "caught", readStackTrace(t)));
  108: 		if (testIdentifier.isContainer()) {
- : 			Long creationMillis = frames.pop();
- : 			printVerticals(theme.end());
- : 			printf(Style.CONTAINER, " %s", testIdentifier.getDisplayName());
- : 			printf(NONE, " finished after %d ms.%n", System.currentTimeMillis() - creationMillis);
- : 			return;
+ 109: 			appendVerticals(output, nestingLevel, theme.end());
+ 110: 			append(output, Style.CONTAINER, " %s", testIdentifier.getDisplayName());
+ 111: 			append(output, NONE, " finished after %d ms.%n", System.currentTimeMillis() - startedMillis);
+ 112: 		}
+ 113: 		else {
+ 114: 			appendDetail(output, nestingLevel, NONE, "duration", "%d ms%n", System.currentTimeMillis() - startedMillis);
+ 115: 			String status = theme.status(testExecutionResult) + " " + testExecutionResult.getStatus();
+ 116: 			appendDetail(output, nestingLevel, Style.valueOf(testExecutionResult), "status", "%s%n", status);
  117: 		}
- : 		printDetail(NONE, "duration", "%d ms%n", System.currentTimeMillis() - executionStartedMillis);
- : 		String status = theme.status(testExecutionResult) + " " + testExecutionResult.getStatus();
- : 		printDetail(Style.valueOf(testExecutionResult), "status", "%s%n", status);
+ 118: 		print(output);
  119: 	}
  120: 
  121: 	@Override
  122: 	public void executionSkipped(TestIdentifier testIdentifier, String reason) {
- : 		printVerticals(theme.entry());
- : 		printf(Style.valueOf(testIdentifier), " %s%n", testIdentifier.getDisplayName());
- : 		printDetails(testIdentifier);
- : 		printDetail(Style.SKIPPED, "reason", reason);
- : 		printDetail(Style.SKIPPED, "status", theme.skipped() + " SKIPPED");
+ 123: 		int nestingLevel = nestingLevel(testIdentifier);
+ 124: 		StringBuilder output = new StringBuilder();
+ 125: 		appendVerticals(output, nestingLevel, theme.entry());
+ 126: 		append(output, Style.valueOf(testIdentifier), " %s%n", testIdentifier.getDisplayName());
+ 127: 		appendDetails(output, nestingLevel, testIdentifier);
+ 128: 		appendDetail(output, nestingLevel, Style.SKIPPED, "reason", reason);
+ 129: 		appendDetail(output, nestingLevel, Style.SKIPPED, "status", theme.skipped() + " SKIPPED");
+ 130: 		print(output);
  131: 	}
  132: 
  133: 	@Override
  134: 	public void dynamicTestRegistered(TestIdentifier testIdentifier) {
- : 		printVerticals(theme.entry());
- : 		printf(Style.DYNAMIC, " %s", testIdentifier.getDisplayName());
- : 		printf(NONE, "%s%n", " dynamically registered");
+ 135: 		StringBuilder output = new StringBuilder();
+ 136: 		appendVerticals(output, nestingLevel(testIdentifier), theme.entry());
+ 137: 		append(output, Style.DYNAMIC, " %s", testIdentifier.getDisplayName());
+ 138: 		append(output, NONE, "%s%n", " dynamically registered");
+ 139: 		print(output);
  140: 	}
  141: 
  142: 	@Override
  143: 	public void reportingEntryPublished(TestIdentifier testIdentifier, ReportEntry entry) {
- : 		printDetail(Style.REPORTED, "reports", entry.toString());
+ 144: 		StringBuilder output = new StringBuilder();
+ 145: 		appendDetail(output, nestingLevel(testIdentifier), Style.REPORTED, "reports", entry.toString());
+ 146: 		print(output);
  147: 	}
  148: 
  149: 	@Override
  150: 	public void fileEntryPublished(TestIdentifier testIdentifier, FileEntry file) {
- : 		printDetail(Style.REPORTED, "reports", file.toString());
+ 151: 		StringBuilder output = new StringBuilder();
+ 152: 		appendDetail(output, nestingLevel(testIdentifier), Style.REPORTED, "reports", file.toString());
+ 153: 		print(output);
  154: 	}
  155: 
  156: 	/**
- : 	 * Print static information about the test identifier.
+ 157: 	 * Append static information about the test identifier.
  158: 	 */
- : 	private void printDetails(TestIdentifier testIdentifier) {
- : 		printDetail(NONE, "tags", "%s%n", testIdentifier.getTags());
- : 		printDetail(NONE, "uniqueId", "%s%n", testIdentifier.getUniqueId());
- : 		printDetail(NONE, "parent", "%s%n", testIdentifier.getParentId().orElse("[]"));
- : 		testIdentifier.getSource().ifPresent(source -> printDetail(NONE, "source", "%s%n", source));
+ 159: 	private void appendDetails(StringBuilder output, int nestingLevel, TestIdentifier testIdentifier) {
+ 160: 		appendDetail(output, nestingLevel, NONE, "tags", "%s%n", testIdentifier.getTags());
+ 161: 		appendDetail(output, nestingLevel, NONE, "uniqueId", "%s%n", testIdentifier.getUniqueId());
+ 162: 		appendDetail(output, nestingLevel, NONE, "parent", "%s%n", testIdentifier.getParentId().orElse("[]"));
+ 163: 		testIdentifier.getSource().ifPresent(
+ 164: 			source -> appendDetail(output, nestingLevel, NONE, "source", "%s%n", source));
  165: 	}
  166: 
- : 	private String verticals() {
- : 		return verticals(frames.size());
+ 167: 	/**
+ 168: 	 * Determine the nesting level of the supplied test identifier, i.e. the number
+ 169: 	 * of its ancestors in the test plan, with test engines being at level 0.
+ 170: 	 */
+ 171: 	private int nestingLevel(TestIdentifier testIdentifier) {
+ 172: 		TestPlan testPlan = requireNonNull(this.testPlan);
+ 173: 		int nestingLevel = 0;
+ 174: 		TestIdentifier current = testIdentifier;
+ 175: 		// roots are the only identifiers without a parent in the test plan, so
+ 176: 		// getParent(...) does not fail for anything else
+ 177: 		while (!testPlan.getRoots().contains(current)) {
+ 178: 			Optional<TestIdentifier> parent = testPlan.getParent(current);
+ 179: 			if (parent.isEmpty()) {
+ 180: 				break;
+ 181: 			}
+ 182: 			current = parent.get();
+ 183: 			nestingLevel++;
+ 184: 		}
+ 185: 		return nestingLevel;
  186: 	}
  187: 
- : 	private String verticals(int index) {
- : 		return verticals[Math.min(index, verticals.length - 1)];
+ 188: 	private String verticals(int nestingLevel) {
+ 189: 		return verticals[Math.min(nestingLevel, verticals.length - 1)];
  190: 	}
  191: 
- : 	private void printVerticals(String tile) {
- : 		printf(NONE, verticals());
- : 		printf(NONE, tile);
+ 192: 	private void appendVerticals(StringBuilder output, int nestingLevel, String tile) {
+ 193: 		append(output, NONE, verticals(nestingLevel));
+ 194: 		append(output, NONE, tile);
  195: 	}
  196: 
- : 	private void printf(Style style, String message, Object... args) {
- : 		out.printf(colorPalette.paint(style, message), args);
+ 197: 	private void append(StringBuilder output, Style style, String message, Object... args) {
+ 198: 		output.append(colorPalette.paint(style, message).formatted(args));
+ 199: 	}
+ 200: 
+ 201: 	/**
+ 202: 	 * Write the output of a single event with a single write so that events printed
+ 203: 	 * concurrently cannot interleave within a line.
+ 204: 	 */
+ 205: 	private void print(StringBuilder output) {
+ 206: 		out.print(output);
  207: 		out.flush();
  208: 	}
  209: 
  210: 	/**
- : 	 * Print single detail with a potential multi-line message.
+ 211: 	 * Append single detail with a potential multi-line message.
  212: 	 */
- : 	private void printDetail(Style style, String detail, String format, Object... args) {
- : 		// print initial verticals - expecting to be at start of the line
- : 		String verticals = verticals(frames.size() + 1);
- : 		printf(NONE, verticals);
+ 213: 	private void appendDetail(StringBuilder output, int nestingLevel, Style style, String detail, String format,
+ 214: 			Object... args) {
+ 215: 		// append initial verticals - expecting to be at start of the line
+ 216: 		String verticals = verticals(nestingLevel + 1);
+ 217: 		append(output, NONE, verticals);
  218: 		String detailFormat = "%9s";
  219: 		// omit detail string if it's empty
  220: 		if (!detail.isEmpty()) {
- : 			printf(NONE, "%s", (detailFormat + ": ").formatted(detail));
+ 221: 			append(output, NONE, "%s", (detailFormat + ": ").formatted(detail));
  222: 		}
- : 		// trivial case: at least one arg is given? Let printf do the entire work
+ 223: 		// trivial case: at least one arg is given? Let the format do the entire work
  224: 		if (args.length > 0) {
- : 			printf(style, format, args);
+ 225: 			append(output, style, format, args);
  226: 			return;
  227: 		}
  228: 		// still here? Split format into separate lines and indent them from the second line on
  229: 		String[] lines = format.split("\\R");
- : 		printf(style, "%s", lines[0]);
+ 230: 		append(output, style, "%s", lines[0]);
  231: 		if (lines.length > 1) {
  232: 			String delimiter = System.lineSeparator() + verticals + (detailFormat + "    ").formatted("");
  233: 			for (int i = 1; i < lines.length; i++) {
- : 				printf(NONE, "%s", delimiter);
- : 				printf(style, "%s", lines[i]);
+ 234: 				append(output, NONE, "%s", delimiter);
+ 235: 				append(output, style, "%s", lines[i]);
  236: 			}
  237: 		}
- : 		printf(NONE, "%n");
+ 238: 		append(output, NONE, "%n");
  239: 	}
  240: 
  241: 	@Override
  242: 	public void listTests(TestPlan testPlan) {
- : 		frames.push(0L);
+ 243: 		this.testPlan = testPlan;
  244: 		testPlan.accept(new TestPlan.Visitor() {
  245: 			@Override
  246: 			public void preVisitContainer(TestIdentifier testIdentifier) {
  247: 				if (!testPlan.getChildren(testIdentifier).isEmpty()) {
- : 					printVerticals(theme.entry());
- : 					printf(Style.CONTAINER, " %s", testIdentifier.getDisplayName());
- : 					printf(NONE, "%n");
- : 					frames.push(0L);
+ 248: 					StringBuilder output = new StringBuilder();
+ 249: 					appendVerticals(output, nestingLevel(testIdentifier), theme.entry());
+ 250: 					append(output, Style.CONTAINER, " %s", testIdentifier.getDisplayName());
+ 251: 					append(output, NONE, "%n");
+ 252: 					print(output);
  253: 				}
  254: 			}
  255: 
  256: 			@Override
  257: 			public void visit(TestIdentifier testIdentifier) {
  258: 				if (testPlan.getChildren(testIdentifier).isEmpty()) {
- : 					printVerticals(theme.entry());
- : 					printf(Style.valueOf(testIdentifier), " %s%n", testIdentifier.getDisplayName());
- : 					printDetails(testIdentifier);
+ 259: 					int nestingLevel = nestingLevel(testIdentifier);
+ 260: 					StringBuilder output = new StringBuilder();
+ 261: 					appendVerticals(output, nestingLevel, theme.entry());
+ 262: 					append(output, Style.valueOf(testIdentifier), " %s%n", testIdentifier.getDisplayName());
+ 263: 					appendDetails(output, nestingLevel, testIdentifier);
+ 264: 					print(output);
  265: 				}
  266: 			}
  267: 
  268: 			@Override
  269: 			public void postVisitContainer(TestIdentifier testIdentifier) {
  270: 				if (!testPlan.getChildren(testIdentifier).isEmpty()) {
- : 					frames.pop();
- : 					printVerticals(theme.end());
- : 					printf(Style.CONTAINER, " %s%n", testIdentifier.getDisplayName());
+ 271: 					StringBuilder output = new StringBuilder();
+ 272: 					appendVerticals(output, nestingLevel(testIdentifier), theme.end());
+ 273: 					append(output, Style.CONTAINER, " %s%n", testIdentifier.getDisplayName());
+ 274: 					print(output);
  275: 				}
  276: 			}
  277: 		});
- : 		frames.pop();
  278: 	}
  279: }
```

**Human:**

> While it is likely that the root of a test plan is also a test identifier without a parent, it would be more accurate for the loop condition to halt when current node has no parent.
> 
> Typically this would be written like this:
> 
> ```
> while ((parent = testPlan.getParent().orElse(null)) != null) {
> ```

**Model:**

> The loop condition in nestingLevel could be simplified. Instead of checking for roots and then getting parent, we could directly check if parent exists and iterate until we reach a root.

---

## M3

**File:** `src/test/java/org/mockitousage/strictness/StrictnessMockAnnotationTest.java`  •  human on line 39, model on line 38

```diff
+ 1: /*
+ 2:  * Copyright (c) 2022 Mockito contributors
+ 3:  * This program is made available under the terms of the MIT License.
+ 4:  */
+ 5: package org.mockitousage.strictness;
+ 6: 
+ 7: import org.assertj.core.api.Assertions;
+ 8: import org.assertj.core.api.ThrowableAssert;
+ 9: import org.junit.Rule;
+ 10: import org.junit.Test;
+ 11: import org.mockito.Mock;
+ 12: import org.mockito.exceptions.misusing.PotentialStubbingProblem;
+ 13: import org.mockito.junit.MockitoJUnit;
+ 14: import org.mockito.junit.MockitoRule;
+ 15: import org.mockito.quality.Strictness;
+ 16: import org.mockitousage.IMethods;
+ 17: 
+ 18: import static org.mockito.Mockito.when;
+ 19: 
+ 20: public class StrictnessMockAnnotationTest {
+ 21: 
+ 22:     public @Rule MockitoRule rule = MockitoJUnit.rule().strictness(Strictness.STRICT_STUBS);
+ 23: 
+ 24:     @Mock(strictness = Strictness.LENIENT)
+ 25:     IMethods lenientMock;
+ 26: 
+ 27:     @Mock IMethods regularMock;
+ 28: 
+ 29:     @Test
+ 30:     public void mock_is_lenient() {
+ 31:         when(lenientMock.simpleMethod("1")).thenReturn("1");
+ 32:         when(regularMock.simpleMethod("2")).thenReturn("2");
+ 33: 
+ 34:         // then lenient mock does not throw:
+ 35:         ProductionCode.simpleMethod(lenientMock, "3");
+ 36: 
+ 37:         // but regular mock throws:
+ 38:         Assertions.assertThatThrownBy(
+ 39:                         new ThrowableAssert.ThrowingCallable() {
+ 40:                             public void call() {
+ 41:                                 ProductionCode.simpleMethod(regularMock, "4");
+ 42:                             }
+ 43:                         })
+ 44:                 .isInstanceOf(PotentialStubbingProblem.class);
+ 45:     }
+ 46: }
```

**Human:**

> Nit: I think we can use a lambda here, can we not?
> 
> ```java
> () -> ProductionCode.simpleMethod(regularMock, "4")
> ```

**Model:**

> The test uses an anonymous inner class for ThrowableAssert.ThrowingCallable. Consider using a lambda expression for better readability.

---

## M4

**File:** `platform-tests/src/test/java/org/junit/platform/reporting/open/xml/OpenTestReportGeneratingListenerTests.java`  •  human on line 353, model on line 352

```diff
  310: 				.selectors(selectUniqueId(UniqueId.forEngine(engine.getId()))) //
  311: 				.enableImplicitConfigurationParameters(false) //
  312: 				.configurationParameter(ENABLED_PROPERTY_NAME, String.valueOf(true)) //
  313: 				.configurationParameter(CAPTURE_STDOUT_PROPERTY_NAME, String.valueOf(true)) //
  314: 				.configurationParameter(CAPTURE_STDERR_PROPERTY_NAME, String.valueOf(true)) //
  315: 				.configurationParameter(OUTPUT_DIR_PROPERTY_NAME, outputDir.toString()) //
  316: 				.configurationParameters(extraConfigurationParameters) //
  317: 				.forExecution() //
  318: 				.listeners(new OpenTestReportGeneratingListener(tempDirectory)) //
  319: 				.build();
  320: 		createLauncher(engine).execute(request);
  321: 	}
  322: 
+ 323: 	@Test
+ 324: 	void writesXmlReportToSocket(@TempDir Path tempDirectory) throws Exception {
+ 325: 		var engine = new DemoHierarchicalTestEngine("dummy");
+ 326: 		engine.addTest("test1", "Test 1", (context, descriptor) -> {
+ 327: 			// Simple test
+ 328: 		});
+ 329: 
+ 330: 		// Start a server socket to receive the XML
+ 331: 		var xmlContent = new AtomicReference<String>();
+ 332: 		var latch = new CountDownLatch(1);
+ 333: 
+ 334: 		try (var serverSocket = new ServerSocket(0)) { // Use any available port
+ 335: 			int port = serverSocket.getLocalPort();
+ 336: 
+ 337: 			// Start a daemon thread to accept the connection and read the XML
+ 338: 			Thread serverThread = new Thread(() -> {
+ 339: 				try (Socket clientSocket = serverSocket.accept();
+ 340: 						var reader = new BufferedReader(
+ 341: 							new InputStreamReader(clientSocket.getInputStream(), StandardCharsets.UTF_8))) {
+ 342: 					var builder = new StringBuilder();
+ 343: 					String line;
+ 344: 					while ((line = reader.readLine()) != null) {
+ 345: 						builder.append(line).append("\n");
+ 346: 					}
+ 347: 					xmlContent.set(builder.toString());
+ 348: 				}
+ 349: 				catch (Exception e) {
+ 350: 					// Only throw if not interrupted during cleanup
+ 351: 					if (!Thread.currentThread().isInterrupted()) {
+ 352: 						throw new RuntimeException(e);
+ 353: 					}
+ 354: 				}
+ 355: 				finally {
+ 356: 					latch.countDown();
+ 357: 				}
+ 358: 			});
+ 359: 			serverThread.setDaemon(true);
+ 360: 			serverThread.start();
+ 361: 
+ 362: 			// Execute tests with socket configuration
+ 363: 			executeTests(tempDirectory, engine, tempDirectory.resolve("junit-reports"),
+ 364: 				Map.of(SOCKET_PROPERTY_NAME, String.valueOf(port)));
+ 365: 
+ 366: 			// Wait for the server to receive the data
+ 367: 			assertThat(latch.await(10, TimeUnit.SECONDS)).isTrue();
+ 368: 
+ 369: 			// Verify XML was received
+ 370: 			assertThat(xmlContent.get()).isNotNull();
+ 371: 			assertThat(xmlContent.get()).contains("<e:events");
+ 372: 			assertThat(xmlContent.get()).contains("dummy");
+ 373: 			assertThat(xmlContent.get()).contains("Test 1");
+ 374: 		}
+ 375: 	}
+ 376: 
  377: }
```

**Human:**

> When is this needed? Can't we just rethrow the exception?
> 
> ```suggestion
> 					fail(e);
> ```

**Model:**

> RuntimeException is thrown in the server thread but not properly propagated to the test, which could lead to silent failures. The test should fail if the server thread encounters an exception.

---

## M5

**File:** `junit-jupiter-api/src/main/java/org/junit/jupiter/api/ClassOrderer.java`  •  human on line 58, model on line 56

```diff
  43:  *
  44:  * <h2>Built-in Implementations</h2>
  45:  *
  46:  * <p>JUnit Jupiter provides the following built-in {@code ClassOrderer}
  47:  * implementations.
  48:  *
  49:  * <ul>
  50:  * <li>{@link ClassOrderer.ClassName}</li>
  51:  * <li>{@link ClassOrderer.DisplayName}</li>
  52:  * <li>{@link ClassOrderer.OrderAnnotation}</li>
  53:  * <li>{@link ClassOrderer.Random}</li>
  54:  * </ul>
  55:  *
+ 56:  * <p>In addition, {@link ClassOrderer.Default} allows reverting back to default ordering for
+ 57:  * {@link Nested @Nested} classes.
+ 58:  *
  59:  * @since 5.8
  60:  * @see TestClassOrder
  61:  * @see ClassOrdererContext
  62:  * @see #orderClasses(ClassOrdererContext)
  63:  * @see MethodOrderer
  64:  */
  65: @API(status = STABLE, since = "5.10")
  66: public interface ClassOrderer {
  67: 
  68: 	/**
  69: 	 * Property name used to set the default class orderer class name: {@value}
  70: 	 *
  71: 	 * <h4>Supported Values</h4>
```

**Human:**

> I would simply list `Default` along with the other implementations in the above list, since the Javadoc for `Default` explains its purpose.
> 
> Plus, we don't explain the purpose of any of the other implementations in the class-level Javadoc.

**Model:**

> The new Default class is mentioned in the documentation but not shown in the built-in implementations list. Consider adding it to the list for consistency.

---
