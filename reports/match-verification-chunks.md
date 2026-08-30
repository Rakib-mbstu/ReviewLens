# RQ1 — match verification, pass 2 (the code)

**Do not open this until pass 1 is complete for all 8 ids.** The diff chunk
the reviewer saw, per sheet id, recovered from the raw request the review
engine sent. Record `verdict_with_code` in `reports/match-verification.csv`.

---

## M1

**File:** `src/main/java/org/mockito/plugins/MockitoPlugins.java`  •  human on line 58, model on line 58

```diff
  31:      */
  32:     <T> T getDefaultPlugin(Class<T> pluginType);
  33: 
  34:     /**
  35:      * Returns inline mock maker, an optional mock maker that is bundled with Mockito distribution.
  36:      * This method is needed because {@link #getDefaultPlugin(Class)} does not provide an instance of inline mock maker.
  37:      * Creates new instance each time is called so it is recommended to keep hold of the resulting object for future invocations.
  38:      * For more information about inline mock maker see the javadoc for main {@link Mockito} class.
  39:      *
  40:      * @return instance of inline mock maker
  41:      * @since 2.10.0
  42:      */
  43:     MockMaker getInlineMockMaker();
+ 44: 
+ 45:     /**
+ 46:      * Returns {@link MockMaker} instance used by Mockito with the passed name {@code mockMaker}.
+ 47:      *
+ 48:      * <p>This will return the instance used by Mockito itself, not a new instance of it.
+ 49:      *
+ 50:      * <p>This method can be used to increase the interop of mocks created by Mockito and other
+ 51:      * libraries using Mockito mock maker API.
+ 52:      *
+ 53:      * @param mockMaker the name of the mock maker or {@code null} to retrieve the default mock maker
+ 54:      * @return instance of the mock maker
+ 55:      * @throws IllegalStateException if a mock maker with the name is not found
+ 56:      * @since 5.6.0
+ 57:      */
+ 58:     MockMaker getMockMaker(String mockMaker);
  59: }
```

**Human:**

> This interface can be implemented, meaning that we can break downstream projects. We should add a default implementation and probably also mark this interface with `@NotExtensible`

**Model:**

> Adding an abstract method to this published interface is a source- and binary-incompatible change for anyone who implements `MockitoPlugins` themselves. Consider giving it a `default` implementation (e.g. throwing `UnsupportedOperationException`) so existing implementors keep compiling.

---

## M2

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

## M3

**File:** `src/main/java/org/mockito/internal/debugging/LocationFactory.java`  •  human on line 26, model on line 27

```diff
  14:     public static Location create() {
  15:         return create(false);
  16:     }
  17: 
  18:     public static Location create(boolean inline) {
  19:         return factory.create(inline);
  20:     }
  21: 
  22:     private interface Factory {
  23:         Location create(boolean inline);
  24:     }
  25: 
  26:     private static Factory createLocationFactory() {
- :         try {
- :             Class.forName("java.lang.StackWalker");
- :             return new Java9PlusLocationFactory();
- :         } catch (ClassNotFoundException e) {
- :             return new Java8LocationFactory();
- :         }
- :     }
- : 
- :     private static final class Java8LocationFactory implements Factory {
- :         @Override
- :         public Location create(boolean inline) {
- :             return new Java8LocationImpl(new Throwable(), inline);
- :         }
- :     }
- : 
- :     private static final class Java9PlusLocationFactory implements Factory {
- : 
- :         @Override
- :         public Location create(boolean inline) {
- :             return new Java9PlusLocationImpl(inline);
- :         }
+ 27:         return (inline) -> new LocationImpl(inline);
  28:     }
  29: }
```

**Human:**

> Nit: this whole factory can now be removed and we can use the relevant location directly

**Model:**

> Now that the factory is a single unconditional lambda, the `Factory` interface, the `factory` field and `createLocationFactory()` no longer buy anything: `create(boolean)` could just `return new LocationImpl(inline);` directly. Consider dropping the indirection along with the JDK-version branching.

---

## M4

**File:** `src/main/java/org/mockito/plugins/MockitoPlugins.java`  •  human on line 58, model on line 58

```diff
  31:      */
  32:     <T> T getDefaultPlugin(Class<T> pluginType);
  33: 
  34:     /**
  35:      * Returns inline mock maker, an optional mock maker that is bundled with Mockito distribution.
  36:      * This method is needed because {@link #getDefaultPlugin(Class)} does not provide an instance of inline mock maker.
  37:      * Creates new instance each time is called so it is recommended to keep hold of the resulting object for future invocations.
  38:      * For more information about inline mock maker see the javadoc for main {@link Mockito} class.
  39:      *
  40:      * @return instance of inline mock maker
  41:      * @since 2.10.0
  42:      */
  43:     MockMaker getInlineMockMaker();
+ 44: 
+ 45:     /**
+ 46:      * Returns {@link MockMaker} instance used by Mockito with the passed name {@code mockMaker}.
+ 47:      *
+ 48:      * <p>This will return the instance used by Mockito itself, not a new instance of it.
+ 49:      *
+ 50:      * <p>This method can be used to increase the interop of mocks created by Mockito and other
+ 51:      * libraries using Mockito mock maker API.
+ 52:      *
+ 53:      * @param mockMaker the name of the mock maker or {@code null} to retrieve the default mock maker
+ 54:      * @return instance of the mock maker
+ 55:      * @throws IllegalStateException if a mock maker with the name is not found
+ 56:      * @since 5.6.0
+ 57:      */
+ 58:     MockMaker getMockMaker(String mockMaker);
  59: }
```

**Human:**

> This interface can be implemented, meaning that we can break downstream projects. We should add a default implementation and probably also mark this interface with `@NotExtensible`

**Model:**

> This adds a new abstract method to a public interface with no default implementation. If any external code implements MockitoPlugins directly, this is a breaking change for them — is that acceptable here, or should this get a default method for compatibility?

---

## M5

**File:** `src/test/java/com/puppycrawl/tools/checkstyle/internal/XdocsExamplesAstConsistencyTest.java`  •  human on line 1159, model on line 1158

```diff
  1111:     }
  1112: 
  1113:     /**
  1114:      * Checks a single example file for block comments used as ok/violation markers.
  1115:      *
  1116:      * @param file the example file to check
  1117:      * @return the list of violation messages
  1118:      * @throws IOException if an I/O error occurs
  1119:      */
  1120:     private static List<String> checkForBlockCommentMarkers(Path file)
  1121:             throws IOException {
  1122:         final List<String> fileViolations = new ArrayList<>();
  1123:         final String content = Files.readString(file);
- :         final Pattern blockCommentPattern = Pattern.compile("(?s)/\\*.*?\\*/");
- :         final Matcher matcher = blockCommentPattern.matcher(content);
+ 1124:         final Matcher matcher = BLOCK_COMMENT_PATTERN.matcher(content);
  1125: 
  1126:         while (matcher.find()) {
  1127:             final String block = matcher.group();
  1128:             final String inner = block
- :                     .replaceAll("^/\\*+", "")
- :                     .replaceAll("\\*/$", "")
- :                     .replace("*", "")
- :                     .strip();
+ 1129:                 .replaceAll("^/\\*+", "")
+ 1130:                 .replaceAll("\\*/$", "")
+ 1131:                 .replace("*", "")
+ 1132:                 .strip();
  1133: 
  1134:             if (inner.startsWith("ok") || inner.startsWith("violation")) {
  1135:                 int lineNo = 1;
  1136:                 for (int index = 0; index < matcher.start(); index++) {
  1137:                     if (content.charAt(index) == '\n') {
  1138:                         lineNo++;
  1139:                     }
  1140:                 }
  1141:                 fileViolations.add(file + ":" + lineNo
- :                         + " - use single-line comment instead: // "
- :                         + inner);
+ 1142:                     + " - use single-line comment instead: // "
+ 1143:                     + inner);
  1144:             }
  1145:         }
  1146:         return fileViolations;
  1147:     }
  1148: 
  1149:     /**
  1150:      * Checks if a directory contains multiple example files.
  1151:      *
  1152:      * @param dir the directory to check
  1153:      * @return true if the directory contains 2 or more Example*.java files
  1154:      */
  1155:     private static boolean containsMultipleExamples(Path dir) {
  1156:         try (Stream<Path> pathStream = Files.list(dir)) {
  1157:             return pathStream
- :                     .filter(path -> path.getFileName().toString().matches("Example\\d+\\.java"))
- :                     .count() > 1;
+ 1158:                 .filter(path -> path.getFileName().toString().matches("Example\\d+\\.java"))
+ 1159:                 .count() > 1;
  1160:         }
  1161:         catch (IOException exception) {
  1162:             throw new IllegalStateException("Failed to list files in directory: " + dir,
- :                     exception);
- :         }
- :     }
- : 
- :     /**
- :      * Checks whether none of the examples in this directory define any module properties.
- :      * When a module has no configurable properties, its examples may intentionally use
- :      * very different code to demonstrate different behaviours, so consistency checking
- :      * is not meaningful.
- :      *
- :      * @param examples the list of example files in the directory
- :      * @return true if no example file contains a {@code <property} element in its XML config
- :      * @throws IOException if an I/O error occurs reading an example file
- :      */
- :     private static boolean isModuleWithNoProperties(List<Path> examples) throws IOException {
- :         boolean result = true;
- :         for (Path example : examples) {
- :             final String content = Files.readString(example);
- :             if (content.contains("<property ")) {
- :                 result = false;
- :                 break;
- :             }
+ 1163:                 exception);
  1164:         }
- :         return result;
  1165:     }
  1166: 
  1167:     /**
  1168:      * Checks examples in a directory. Non-independent examples must match.
  1169:      *
  1170:      * @param dir the directory containing example files
  1171:      * @return list of violation messages for mismatches
  1172:      * @throws IOException if an I/O error occurs
  1173:      */
  1174:     private static List<Violation> checkExamplesInDirectory(Path dir) throws IOException {
  1175:         final List<Violation> violations = new ArrayList<>();
  1176:         final List<Path> examples = getExampleFiles(dir);
  1177:
```

**Human:**

> pleas revert all unrelated to functional fix formatting changes.

**Model:**

> These lines are pure re-indentation of `containsMultipleExamples`, which this PR otherwise does not change. Unrelated formatting churn inflates the diff; consider leaving untouched methods alone.

---

## M6

**File:** `junit-platform-launcher/src/main/java/org/junit/platform/launcher/TestIdentifier.java`  •  human on line 47, model on line 45

```diff
  7:  *
  8:  * https://www.eclipse.org/legal/epl-v20.html
  9:  */
  10: 
  11: package org.junit.platform.launcher;
  12: 
  13: import static java.util.Collections.emptySet;
  14: import static java.util.Collections.singleton;
  15: import static java.util.Collections.unmodifiableSet;
  16: import static org.apiguardian.api.API.Status.INTERNAL;
  17: import static org.apiguardian.api.API.Status.STABLE;
  18: import static org.junit.platform.commons.util.CollectionUtils.getOnlyElement;
  19: 
- : import java.io.IOException;
- : import java.io.ObjectInputStream;
- : import java.io.ObjectOutputStream;
- : import java.io.ObjectStreamClass;
- : import java.io.ObjectStreamField;
- : import java.io.Serial;
- : import java.io.Serializable;
  20: import java.util.LinkedHashSet;
  21: import java.util.Objects;
  22: import java.util.Optional;
  23: import java.util.Set;
  24: 
  25: import org.apiguardian.api.API;
  26: import org.jspecify.annotations.Nullable;
  27: import org.junit.platform.commons.util.Preconditions;
  28: import org.junit.platform.commons.util.ToStringBuilder;
  29: import org.junit.platform.engine.TestDescriptor;
  30: import org.junit.platform.engine.TestDescriptor.Type;
  31: import org.junit.platform.engine.TestSource;
  32: import org.junit.platform.engine.TestTag;
  33: import org.junit.platform.engine.UniqueId;
  34: 
  35: /**
  36:  * Immutable data transfer object that represents a test or container which is
  37:  * usually part of a {@link TestPlan}.
  38:  *
  39:  * @since 1.0
  40:  * @see TestPlan
  41:  */
  42: @API(status = STABLE, since = "1.0")
- : public final class TestIdentifier implements Serializable {
- : 
- : 	@Serial
- : 	private static final long serialVersionUID = 1L;
- : 	@Serial
- : 	@SuppressWarnings("UnusedVariable")
- : 	private static final ObjectStreamField[] serialPersistentFields = ObjectStreamClass.lookup(
- : 		SerializedForm.class).getFields();
+ 43: public final class TestIdentifier {
  44: 
  45: 	// These are effectively final but not technically due to late initialization when deserializing
  46: 	private /* final */ UniqueId uniqueId;
  47: 
  48: 	private /* final */ @Nullable UniqueId parentId;
  49: 
  50: 	private /* final */ String displayName;
  51: 	private /* final */ String legacyReportingName;
  52: 
  53: 	private /* final */ @Nullable TestSource source;
  54: 	private /* final */ Set<TestTag> tags;
  55: 	private /* final */ Type type;
  56:
```

**Human:**

> This is no longer the case. Please remove this comment and convert `/* final */` to `final` on all fields.
> 
> ```suggestion
> 	private final UniqueId uniqueId;
> ```

**Model:**

> Now that late initialization during deserialization is gone, the comment "effectively final but not technically due to late initialization when deserializing" no longer holds; these fields can be declared `final` and the `/* final */` markers dropped.

---

## M7

**File:** `src/main/java/com/puppycrawl/tools/checkstyle/checks/javadoc/JavadocTypeCheck.java`  •  human on line 421, model on line 421

```diff
  408:                                         Collection<JavadocTag> tags,
  409:                                         String recordComponentName) {
  410: 
  411:         final boolean found = tags
  412:             .stream()
  413:                 .filter(JavadocTag::isParamTag).anyMatch(tag -> {
  414:                     final String arg = tag.getFirstArg();
  415:                     return arg.equals(recordComponentName)
  416:                             || arg.startsWith(recordComponentName + SPACE);
  417:                 });
  418: 
  419:         if (!found) {
  420:             log(ast, MSG_MISSING_TAG, JavadocTagInfo.PARAM.getText()
- :                 + SPACE + recordComponentName);
+ 421:                 + SPACE + APOSTROPHE + recordComponentName + APOSTROPHE);
  422:         }
  423:     }
  424: 
  425:     /**
  426:      * Verifies that a type definition has the specified param tag for
  427:      * the specified type parameter name.
  428:      *
  429:      * @param ast the AST node for the type definition.
  430:      * @param tags tags from the Javadoc comment for the type definition.
  431:      * @param typeParamName the name of the type parameter
  432:      */
  433:     private void checkTypeParamTag(DetailAST ast,
  434:             Collection<JavadocTag> tags, String typeParamName) {
```

**Human:**

> Can you refer to https://github.com/checkstyle/checkstyle/pull/19809#discussion_r3240257202 ? The Apostrophe thing does work, but why not just fix it from the violation message itself? Even this has `+ SPACE` which is hacky.

**Model:**

> The quoting is assembled at the call site by concatenating APOSTROPHE around the argument. Putting the quotes in the MSG_MISSING_TAG message property instead (as ''{0}'' in the properties file) would keep the formatting with the message text and avoid growing this concatenation chain further.

---

## M8

**File:** `junit-jupiter-migrationsupport/src/main/java/org/junit/jupiter/migrationsupport/EnableJUnit4MigrationSupport.java`  •  human on line 53, model on line 55

```diff
  38:  * annotation which registers all of the following migration extensions:
  39:  * {@link VerifierSupport}, {@link ExternalResourceSupport},
  40:  * {@link ExpectedExceptionSupport}, and {@link IgnoreCondition}. Note, however,
  41:  * that you can optionally register one or more of these extensions explicitly
  42:  * without the use of this composed annotation.
  43:  *
  44:  * @since 5.4
  45:  * @see ExternalResourceSupport
  46:  * @see VerifierSupport
  47:  * @see ExpectedExceptionSupport
  48:  * @see IgnoreCondition
  49:  * @see EnableRuleMigrationSupport
  50:  */
+ 51: @SuppressWarnings("removal")
  52: @Target(ElementType.TYPE)
  53: @Retention(RetentionPolicy.RUNTIME)
- : @API(status = STABLE, since = "5.7")
+ 54: @API(status = DEPRECATED, since = "6.0")
+ 55: @Deprecated(since = "6.0", forRemoval = true)
  56: @EnableRuleMigrationSupport
  57: @ExtendWith(IgnoreCondition.class)
  58: public @interface EnableJUnit4MigrationSupport {
  59: }
```

**Human:**

> Missing `@deprecated` Javadoc tag

**Model:**

> The annotation is now @Deprecated(forRemoval = true) but the Javadoc above has no @deprecated tag. For a public API marked for removal, add a @deprecated paragraph naming the replacement (e.g. Jupiter's @Disabled and the native extension model) so the compiler warning points users somewhere.

---
