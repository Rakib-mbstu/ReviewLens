# Hallucination screen — human verification slice

46 judgments, seed 20260826. Stratified, not uniform: weighted toward the
verdicts where a biased judge would do the most damage (see
`work/halluc/build_human_slice.py` for why).

**The machine's verdict is deliberately not shown.** Judge each comment against
the chunk on its own, then record `founded` / `unfounded` / `unverifiable` in
`reports/hallucination-human-slice.csv` against the matching id.

Definitions are in `prompts/hallucination_v1.md` — the same rubric the machine got.

---

## 1. `claude-code-subagent__opus__mockito__mockito__2659__unmatched_model__4`

**Arm:** `opus`  •  **File:** `src/main/java/org/mockito/internal/configuration/MockAnnotationProcessor.java`  •  **comment on line 52**  •  [PR #2659](https://github.com/mockito/mockito/pull/2659)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  18: import org.mockito.exceptions.base.MockitoException;
  19: import org.mockito.internal.util.Supplier;
  20: 
  21: /**
  22:  * Instantiates a mock on a field annotated by {@link Mock}
  23:  */
  24: public class MockAnnotationProcessor implements FieldAnnotationProcessor<Mock> {
  25:     @Override
  26:     public Object process(Mock annotation, Field field) {
  27:         return processAnnotationForMock(
  28:                 annotation, field.getType(), field::getGenericType, field.getName());
  29:     }
  30: 
+ 31:     @SuppressWarnings("deprecation")
  32:     public static Object processAnnotationForMock(
  33:             Mock annotation, Class<?> type, Supplier<Type> genericType, String name) {
  34:         MockSettings mockSettings = Mockito.withSettings();
  35:         if (annotation.extraInterfaces().length > 0) { // never null
  36:             mockSettings.extraInterfaces(annotation.extraInterfaces());
  37:         }
  38:         if ("".equals(annotation.name())) {
  39:             mockSettings.name(name);
  40:         } else {
  41:             mockSettings.name(annotation.name());
  42:         }
  43:         if (annotation.serializable()) {
  44:             mockSettings.serializable();
  45:         }
  46:         if (annotation.stubOnly()) {
  47:             mockSettings.stubOnly();
  48:         }
- :         mockSettings.strictness(annotation.strictness());
  49:         if (annotation.lenient()) {
  50:             mockSettings.lenient();
  51:         }
+ 52:         if (annotation.strictness() != Mock.Strictness.NOT_SET) {
+ 53:             mockSettings.strictness(annotation.strictness().outer());
+ 54:         }
  55: 
  56:         // see @Mock answer default value
  57:         mockSettings.defaultAnswer(annotation.answer());
  58: 
  59:         if (type == MockedStatic.class) {
  60:             return Mockito.mockStatic(
  61:                     inferParameterizedType(
  62:                             genericType.get(), name, MockedStatic.class.getSimpleName()),
  63:                     mockSettings);
  64:         } else if (type == MockedConstruction.class) {
  65:             return Mockito.mockConstruction(
  66:                     inferParameterizedType(
  67:                             genericType.get(), name, MockedConstruction.class.getSimpleName()),
```

**The reviewer's comment:**

> If a field carries both the deprecated lenient() and an explicit strictness(), lenient() is applied first and then silently overwritten here. Should that combination be rejected with a clear misuse error instead of picking a winner quietly?

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 2. `claude-code-subagent__opus__mockito__mockito__3097__unmatched_model__5`

**Arm:** `opus`  •  **File:** `src/test/java/org/mockito/internal/stubbing/defaultanswers/ReturnsOptionalMocksTest.java`  •  **comment on line 71**  •  [PR #3097](https://github.com/mockito/mockito/pull/3097)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2:  * Copyright (c) 2023 Mockito contributors
+ 3:  * This program is made available under the terms of the MIT License.
+ 4:  */
+ 5: package org.mockito.internal.stubbing.defaultanswers;
+ 6: 
+ 7: import static org.assertj.core.api.Assertions.assertThat;
+ 8: import static org.mockito.Mockito.RETURNS_DEEP_STUBS;
+ 9: import static org.mockito.Mockito.mock;
+ 10: import static org.mockito.Mockito.mockingDetails;
+ 11: import static org.mockito.Mockito.times;
+ 12: import static org.mockito.Mockito.verify;
+ 13: import static org.mockito.Mockito.when;
+ 14: 
+ 15: import java.util.Optional;
+ 16: import java.util.OptionalDouble;
+ 17: import java.util.OptionalInt;
+ 18: import java.util.OptionalLong;
+ 19: 
+ 20: import org.junit.Test;
+ 21: 
+ 22: public class ReturnsOptionalMocksTest {
+ 23:     private interface Type {
+ 24:         Optional<String> getOptString();
+ 25: 
+ 26:         OptionalLong getOptLong();
+ 27: 
+ 28:         OptionalDouble getOptDouble();
+ 29: 
+ 30:         OptionalInt getOptInt();
+ 31:     }
+ 32: 
+ 33:     @Test
+ 34:     public void deepStubs_Optional_should_return_mocked_optional_Issue2865() {
+ 35:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 36:         assertThat(type.getOptString()).isNotEqualTo(Optional.empty());
+ 37:         assertIsMock(type.getOptString());
+ 38:     }
+ 39: 
+ 40:     @Test
+ 41:     public void deepStubs_OptionalLong_should_return_mocked_optional_Issue2865() {
+ 42:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 43:         assertThat(type.getOptLong()).isNotEqualTo(OptionalLong.empty());
+ 44:         assertIsMock(type.getOptLong());
+ 45:     }
+ 46: 
+ 47:     @Test
+ 48:     public void deepStubs_OptionalDouble_should_return_mocked_optional_Issue2865() {
+ 49:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 50:         assertThat(type.getOptDouble()).isNotEqualTo(OptionalDouble.empty());
+ 51:         assertIsMock(type.getOptDouble());
+ 52:     }
+ 53: 
+ 54:     @Test
+ 55:     public void deepStubs_OptionalInt_should_return_mocked_optional() {
+ 56:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 57:         assertThat(type.getOptInt()).isNotEqualTo(OptionalInt.empty());
+ 58:         assertIsMock(type.getOptInt());
+ 59:     }
+ 60: 
+ 61:     @Test
+ 62:     public void normal_mock_Optional_should_return_normal_optional_empty() {
+ 63:         final Type type = mock(Type.class);
+ 64:         assertThat(type.getOptString()).isEqualTo(Optional.empty());
+ 65:         assertIsNoMock(type.getOptString());
+ 66:     }
+ 67: 
+ 68:     @Test
+ 69:     public void normal_mock_OptionalLong_should_return_normal_optional_empty() {
+ 70:         final Type type = mock(Type.class);
+ 71:         assertThat(type.getOptLong()).isEqualTo(OptionalLong.empty());
+ 72:     }
+ 73: 
+ 74:     @Test
+ 75:     public void normal_mock_OptionalDouble_should_return_normal_optional_empty() {
+ 76:         final Type type = mock(Type.class);
+ 77:         assertThat(type.getOptDouble()).isEqualTo(OptionalDouble.empty());
+ 78:     }
+ 79: 
+ 80:     @Test
+ 81:     public void normal_mock_OptionalInt_should_return_normal_optional_empty() {
+ 82:         final Type type = mock(Type.class);
+ 83:         assertThat(type.getOptInt()).isEqualTo(OptionalInt.empty());
+ 84:     }
+ 85: 
+ 86:     @Test
+ 87:     public void deepStubs_Optional_isPresent_isEmpty_Issue2865() {
+ 88:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 89:         Optional<String> opt = type.getOptString();
+ 90:         assertThat(opt.isPresent()).isEqualTo(false);
+ 91:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 92:     }
+ 93: 
+ 94:     @Test
+ 95:     public void deepStubs_Optional_isEmpty_is_mockable() {
+ 96:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 97:         Optional<String> opt = type.getOptString();
+ 98:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 99:         when(opt.isEmpty()).thenReturn(false);
+ 100:         assertThat(opt.isEmpty()).isEqualTo(false);
+ 101:         verify(opt, times(2)).isEmpty();
+ 102:     }
+ 103: 
+ 104:     @Test
+ 105:     public void deepStubs_OptionalLong_isPresent_isEmpty_Issue2865() {
+ 106:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 107:         OptionalLong opt = type.getOptLong();
+ 108:         assertThat(opt.isPresent()).isEqualTo(false);
+ 109:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 110:     }
+ 111: 
+ 112:     @Test
+ 113:     public void deepStubs_OptionalDouble_isPresent_isEmpty_Issue2865() {
+ 114:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 115:         OptionalDouble opt = type.getOptDouble();
+ 116:         assertThat(opt.isPresent()).isEqualTo(false);
+ 117:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 118:     }
+ 119: 
+ 120:     @Test
+ 121:     public void deepStubs_OptionalInt_isPresent_isEmpty_Issue2865() {
+ 122:         final Type type = mock(Type.class, RETURNS_DEEP_STUBS);
+ 123:         OptionalInt opt = type.getOptInt();
+ 124:         assertThat(opt.isPresent()).isEqualTo(false);
+ 125:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 126:     }
+ 127: 
+ 128:     @Test
+ 129:     public void normal_mock_Optional_isPresent_isEmpty_Issue2865() {
+ 130:         final Type type = mock(Type.class);
+ 131: 
+ 132:         Optional<String> opt = type.getOptString();
+ 133:         assertThat(opt.isPresent()).isEqualTo(false);
+ 134:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 135:     }
+ 136: 
+ 137:     @Test
+ 138:     public void normal_mock_OptionalLong_isPresent_isEmpty_Issue2865() {
+ 139:         final Type type = mock(Type.class);
+ 140: 
+ 141:         OptionalLong opt = type.getOptLong();
+ 142:         assertThat(opt.isPresent()).isEqualTo(false);
+ 143:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 144:     }
+ 145: 
+ 146:     @Test
+ 147:     public void normal_mock_OptionalDouble_isPresent_isEmpty_Issue2865() {
+ 148:         final Type type = mock(Type.class);
+ 149: 
+ 150:         OptionalDouble opt = type.getOptDouble();
+ 151:         assertThat(opt.isPresent()).isEqualTo(false);
+ 152:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 153:     }
+ 154: 
+ 155:     @Test
+ 156:     public void normal_mock_OptionalInt_isPresent_isEmpty_Issue2865() {
+ 157:         final Type type = mock(Type.class);
+ 158: 
+ 159:         OptionalInt opt = type.getOptInt();
+ 160:         assertThat(opt.isPresent()).isEqualTo(false);
+ 161:         assertThat(opt.isEmpty()).isEqualTo(true);
+ 162:     }
+ 163: 
+ 164:     private void assertIsMock(Object mock) {
+ 165:         assertThat(mockingDetails(mock).isMock()).isTrue();
+ 166:     }
+ 167: 
+ 168:     private void assertIsNoMock(Object mock) {
+ 169:         assertThat(mockingDetails(mock).isMock()).isFalse();
+ 170:     }
+ 171: }
```

**The reviewer's comment:**

> The `Optional` variant also asserts `assertIsNoMock(...)`, but the Long/Double/Int variants only compare to `empty()`. Adding the same mock check here would make the four normal-mock tests actually equivalent.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 3. `anthropic__claude-sonnet-5__checkstyle__checkstyle__20537__unmatched_model__2`

**Arm:** `sonnet`  •  **File:** `src/main/java/com/puppycrawl/tools/checkstyle/checks/coding/UnusedLocalVariableCheck.java`  •  **comment on line 452**  •  [PR #20537](https://github.com/checkstyle/checkstyle/pull/20537)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  432:     }
  433: 
  434:     /**
  435:      * Add a pattern variable to the {@code variablesStack} stack.
  436:      *
  437:      * @param patternVarDefAst ast of type {@link TokenTypes#PATTERN_VARIABLE_DEF}
  438:      * @param variablesStack stack of all the relevant variables in the scope
  439:      */
  440:     private static void addPatternVariable(DetailAST patternVarDefAst,
  441:             Deque<VariableDesc> variablesStack) {
  442:         final DetailAST ident = patternVarDefAst.findFirstToken(TokenTypes.IDENT);
  443:         final DetailAST scope = findScopeOfPatternVariable(patternVarDefAst);
  444:         final VariableDesc desc = new VariableDesc(ident.getText(), ident, scope);
- :         if (isSwitchCasePatternVariable(patternVarDefAst)) {
+ 445:         if (isForcedNamePatternVariable(patternVarDefAst)) {
  446:             desc.registerAsNamedPatternVar();
  447:         }
  448:         variablesStack.push(desc);
  449:     }
  450: 
  451:     /**
- :      * Checks whether the pattern variable is declared in a switch labels.
+ 452:      * Checks whether the pattern variable is declared in a switch labels and instanceof.
  453:      *
  454:      * @param patternVarDefAst ast of type {@link TokenTypes#PATTERN_VARIABLE_DEF}
- :      * @return true if the pattern variable is declared in a switch label
+ 455:      * @return true if the pattern variable is in a forced-name context
  456:      */
- :     private static boolean isSwitchCasePatternVariable(DetailAST patternVarDefAst) {
- :         DetailAST current = patternVarDefAst;
- :         while (current != null
- :                 && current.getType() != TokenTypes.LITERAL_CASE) {
- :             current = current.getParent();
- :         }
- :         return current != null;
+ 457:     private static boolean isForcedNamePatternVariable(DetailAST patternVarDefAst) {
+ 458:         return patternVarDefAst.getParent().getType() != TokenTypes.LITERAL_INSTANCEOF;
  459:     }
  460: 
  461:     /**
  462:      * Find the scope of a pattern variable.
  463:      *
  464:      * @param patternVarDefAst ast of type.
  465:      * @return the outermost enclosing {@link TokenTypes#SLIST}, or {@code null} if none.
  466:      */
  467:     private static DetailAST findScopeOfPatternVariable(DetailAST patternVarDefAst) {
  468:         final Deque<DetailAST> slistAncestors = new ArrayDeque<>();
  469:         for (DetailAST current = patternVarDefAst;
  470:              current != null;
  471:              current = current.getParent()) {
```

**The reviewer's comment:**

> Javadoc wording is awkward: "declared in a switch labels and instanceof" has a singular/plural mismatch and doesn't clearly convey that record-pattern destructuring inside instanceof is also covered. Consider rewording, e.g. 'declared in a switch label or as part of instanceof record-pattern destructuring'.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 4. `claude-code-subagent__opus__checkstyle__checkstyle__20537__unmatched_model__4`

**Arm:** `opus`  •  **File:** `src/main/java/com/puppycrawl/tools/checkstyle/checks/coding/UnusedLocalVariableCheck.java`  •  **comment on line 1104**  •  [PR #20537](https://github.com/checkstyle/checkstyle/pull/20537)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  1090:         /* package */ void registerAsUsed() {
  1091:             used = true;
  1092:         }
  1093: 
  1094:         /**
  1095:          * Register the variable as an instance variable or
  1096:          * class variable.
  1097:          */
  1098:         /* package */ void registerAsInstOrClassVar() {
  1099:             instVarOrClassVar = true;
  1100:         }
  1101: 
  1102:         /**
- :          * Register the variable as a named pattern variable
- :          * declared in a switch label.
+ 1103:          * Register the variable as a forced-name pattern variable declared
+ 1104:          * in a switch label or instanceof record Destructuring.
  1105:          */
  1106:         /* package */ void registerAsNamedPatternVar() {
  1107:             namedPatternVar = true;
  1108:         }
  1109: 
  1110:         /**
  1111:          * Is the variable used or not.
  1112:          *
  1113:          * @return true if variable is used
  1114:          */
  1115:         /* package */ boolean isUsed() {
  1116:             return used;
  1117:         }
  1118: 
  1119:         /**
  1120:          * Is an instance variable or a class variable.
  1121:          *
  1122:          * @return true if is an instance variable or a class variable
  1123:          */
  1124:         /* package */ boolean isInstVarOrClassVar() {
  1125:             return instVarOrClassVar;
  1126:         }
  1127: 
  1128:         /**
- :          * Is a named pattern variable from a switch label.
+ 1129:          * Is a forced-name pattern variable from a switch label or
+ 1130:          * instanceof record Destructuring.
  1131:          *
- :          * @return true if this variable was declared via a
- :          *         {@link TokenTypes#PATTERN_VARIABLE_DEF} with a non-underscore name
- :          *         in a switch label
+ 1132:          * @return true if this variable was declared in a context where
+ 1133:          *         pre-JDK 22 forces a name to be given even when unused
  1134:          */
  1135:         /* package */ boolean isNamedPatternVar() {
  1136:             return namedPatternVar;
  1137:         }
  1138:     }
  1139: 
  1140:     /**
  1141:      * Maintains information about the type declaration.
  1142:      * Any ast node of type {@link TokenTypes#CLASS_DEF} or {@link TokenTypes#INTERFACE_DEF}
  1143:      * or {@link TokenTypes#ENUM_DEF} or {@link TokenTypes#ANNOTATION_DEF}
  1144:      * or {@link TokenTypes#RECORD_DEF} is considered as a type declaration.
  1145:      */
  1146:     private static final class TypeDeclDesc {
```

**The reviewer's comment:**

> `instanceof record Destructuring` capitalizes 'Destructuring' mid-sentence; use lowercase 'destructuring' (or 'record deconstruction patterns') to match the surrounding prose.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 5. `claude-code-subagent__opus__checkstyle__checkstyle__20554__unmatched_model__8`

**Arm:** `opus`  •  **File:** `src/xdocs-examples/resources/com/puppycrawl/tools/checkstyle/checks/todocomment/Example3.java`  •  **comment on line 52**  •  [PR #20554](https://github.com/checkstyle/checkstyle/pull/20554)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  4:     <module name="TodoComment">
  5:       <property name="id" value="BoxComments"/>
  6:       <property name="format" value="^\s*([*=#])\1{8,}\s*$"/>
  7:       <message key="todo.match"
  8:                value="Comment uses box-like repetitive character pattern."/>
  9:     </module>
  10:   </module>
  11: </module>
  12: */
  13: 
  14: package com.puppycrawl.tools.checkstyle.checks.todocomment;
  15: 
  16: // xdoc section -- start
- : /** // violation 'Comment uses box-like repetitive character pattern'
+ 17: // violation below 'Comment uses box-like repetitive character pattern'
+ 18: /**
  19:  =========================================
  20:  Box comment with equals
  21:  =========================================
  22:  */
- : 
  23: public class Example3 {
+ 24:   int i;
+ 25:   int x;
  26: 
- :   // violation below 'Comment uses box-like repetitive character pattern'
  27:   // =========
- :   void method1() {
- :     int y = 2;
- :   }
+ 28:   // violation above 'Comment uses box-like repetitive character pattern'
+ 29:   public void test() {
+ 30:     // TODO: do differently in future
+ 31: 
+ 32:     i++;
  33: 
- :   // violation below 'Comment uses box-like repetitive character pattern'
+ 34:     // todo: do differently in future
+ 35: 
+ 36:     i++;
+ 37: 
+ 38:     // FIXME: handle x = 0 case
+ 39: 
+ 40:     i = i / x;
+ 41:   }
  42:   // *********
- :   void method2() {
- :     int z = 3;
+ 43:   // violation above 'Comment uses box-like repetitive character pattern'
+ 44:   public void method1() {
+ 45:     int y = 2;
  46:   }
- : 
- :   // violation below 'Comment uses box-like repetitive character pattern'
  47:   // #########
- :   void method3() {
- :     int a = 4;
+ 48:   // violation above 'Comment uses box-like repetitive character pattern'
+ 49:   public void method2() {
+ 50:     int z = 3;
  51:   }
- : 
- :   // normal comment
- :   void method4() {
+ 52:   // ###### (only 6 chars)
+ 53:   public void method4() {
  54:     int b = 5;
  55:   }
- : 
- :   // ###### (only 6 chars - below 9-char threshold)
- :   void method5() {
- :     int c = 6;
- :   }
  56: }
  57: // xdoc section -- end
```

**The reviewer's comment:**

> The comment lost the `- below 9-char threshold` explanation it previously carried. That parenthetical was what told the reader why 6 repeated characters do not match `^\s*([*=#])\1{8,}\s*$`; keep it so the negative case still explains itself.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 6. `anthropic__claude-sonnet-5__checkstyle__checkstyle__21086__unmatched_model__0`

**Arm:** `sonnet`  •  **File:** `src/main/resources/com/puppycrawl/tools/checkstyle/checks/javadoc/messages_pt.properties`  •  **comment on line 25**  •  [PR #21086](https://github.com/checkstyle/checkstyle/pull/21086)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  2: invalid.position=O comentário Javadoc está colocado no local errado.
  3: javadoc.asterisk.indentation=O asterisco inicial tem nível de recuo {0} incorreto, o esperado é {1}.
  4: javadoc.blockTagLocation=A tag de bloco Javadoc ''@{0}'' deveria ser colocada no início da linha.
  5: javadoc.classInfo=Não foi possível obter informações de classe para {0} tag ''{1}''.
  6: javadoc.content.first.line=O conteúdo Javadoc deveria começar da mesma linha que o /**.
  7: javadoc.content.second.line=O conteúdo Javadoc deveria começar a partir da próxima linha depois do /**.
  8: javadoc.duplicateTag=A tag ''{0}'' está duplicada.
  9: javadoc.expectedTag=Esperada a tag {0} para ''{1}''.
  10: javadoc.invalidInheritDoc=Uso inválido da tag ''@inheritDoc''.
  11: javadoc.legacyPackageHtml=O arquivo package.html legado deve ser removido.
  12: javadoc.missing=Falta o comentário Javadoc.
  13: javadoc.missing.asterisk=A linha Javadoc deveria começar com um asterisco inicial.
  14: javadoc.missing.whitespace=Falta um espaço em branco após o asterisco inicial.
+ 15: javadoc.missingTag=O comentário Javadoc está com uma tag {0} faltando.
  16: javadoc.packageInfo=O arquivo package-info.java está faltando.
  17: javadoc.paragraph.line.before=A tag <p> deveria ser precedida por uma linha vazia.
  18: javadoc.paragraph.misplaced.tag=A tag <p> deveria ser colocada imediatamente antes da primeira palavra, sem espaço depois.
  19: javadoc.paragraph.preceded.block.tag=A tag <p> não deve preceder a tag de bloco HTML ''<{0}>'', a tag <p> deve ser removida.
  20: javadoc.paragraph.redundant.paragraph=Tag <p> redundante.
  21: javadoc.paragraph.tag.after=A linha vazia deveria ser seguida por uma tag <p> na linha seguinte.
  22: javadoc.parse.rule.error=O comentário Javadoc na coluna {0} tem um erro sintático. Detalhes: {1} ao analisar {2}
  23: javadoc.return.expected=A tag @return deve estar presente e ter uma descrição.
  24: javadoc.tag.line.before=Javadoc tag ''{0}'' deve ser precedido com uma linha vazia.
+ 25: javadoc.tagFormat=O formato da tag Javadoc {0} deveria condizer com o padrão ''{1}''
  26: javadoc.unclosedHtml=Encontrada uma etiqueta HTML não fechada: {0}
  27: javadoc.unknownTag=Tag desconhecida ''{0}''.
  28: javadoc.unusedTag=Tag {0} não utilizada pelo ''{1}''.
  29: javadoc.unusedTagGeneral=A tag Javadoc não é utilizada.
  30: javadoc.writeTag=Tag javadoc {0}={1}
  31: non.empty.atclause=A cláusula ''@'' deve ter uma descrição não-vazia.
  32: package.javadoc.missing=Falta o Javadoc para o arquivo package-info.java.
  33: singleline.javadoc=O comentário Javadoc de uma só linha deveria ser de múltiplas linhas.
  34: summary.first.sentence=A primeira frase do Javadoc está com o ponto final faltando.
  35: summary.javaDoc=Fragmento de resumo de Javadoc proibido.
  36: summary.javaDoc.missing=O resumo do Javadoc está ausente.
  37: summary.javaDoc.missing.period=O resumo do Javadoc está sem um ponto final.
  38: tag.continuation.indent=Continuação de linha têm um nível de indentação incorreto. O nível esperado era {0}.
```

**The reviewer's comment:**

> This new translation is missing the trailing period that the English source ("...pattern ''{1}''.") and every other message in this file end with: "...deveria condizer com o padrão ''{1}''" has no closing ".".

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 7. `claude-code-subagent__opus__junit-team__junit5__5379__unmatched_model__6`

**Arm:** `opus`  •  **File:** `junit-jupiter-engine/src/main/java/org/junit/jupiter/engine/config/CachingJupiterConfiguration.java`  •  **comment on line 124**  •  [PR #5379](https://github.com/junit-team/junit5/pull/5379)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  110: 		return (ExecutionMode) cache.computeIfAbsent(DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME,
  111: 			__ -> delegate.getDefaultClassesExecutionMode());
  112: 	}
  113: 
  114: 	@Override
  115: 	public TestInstance.Lifecycle getDefaultTestInstanceLifecycle() {
  116: 		return (TestInstance.Lifecycle) cache.computeIfAbsent(DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME,
  117: 			__ -> delegate.getDefaultTestInstanceLifecycle());
  118: 	}
  119: 
  120: 	@SuppressWarnings("unchecked")
  121: 	@Override
  122: 	public Predicate<ExecutionCondition> getExecutionConditionFilter() {
- : 		return (Predicate<ExecutionCondition>) cache.computeIfAbsent(DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME,
- : 			__ -> delegate.getExecutionConditionFilter());
+ 123: 		return (Predicate<ExecutionCondition>) cache.computeIfAbsent(
+ 124: 			Constants.DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME, __ -> delegate.getExecutionConditionFilter());
  125: 	}
  126: 
  127: 	@Override
  128: 	public DisplayNameGenerator getDefaultDisplayNameGenerator() {
  129: 		return (DisplayNameGenerator) cache.computeIfAbsent(DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME,
  130: 			__ -> delegate.getDefaultDisplayNameGenerator());
  131: 	}
  132: 
  133: 	@SuppressWarnings("unchecked")
  134: 	@Override
  135: 	public Optional<MethodOrderer> getDefaultTestMethodOrderer() {
  136: 		return (Optional<MethodOrderer>) cache.computeIfAbsent(DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME,
  137: 			__ -> delegate.getDefaultTestMethodOrderer());
```

**The reviewer's comment:**

> The neighbouring methods pass the cache key as a statically imported constant (e.g. DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME); this one qualifies it as Constants.DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME. A static import here would keep the file consistent and also let the call fit on a single line again.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 8. `claude-code-subagent__opus__checkstyle__checkstyle__20717__unmatched_model__2`

**Arm:** `opus`  •  **File:** `src/test/java/com/puppycrawl/tools/checkstyle/checks/design/InnerTypeLastCheckTest.java`  •  **comment on line 167**  •  [PR #20717](https://github.com/checkstyle/checkstyle/pull/20717)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  131:     @Test
  132:     public void testGetAcceptableTokens() {
  133:         final InnerTypeLastCheck obj = new InnerTypeLastCheck();
  134:         final int[] expected = {
  135:             TokenTypes.CLASS_DEF,
  136:             TokenTypes.INTERFACE_DEF,
  137:             TokenTypes.RECORD_DEF,
  138:         };
  139:         assertWithMessage("Default acceptable tokens are invalid")
  140:             .that(obj.getAcceptableTokens())
  141:             .isEqualTo(expected);
  142:     }
  143: 
+ 144:     @Test
+ 145:     public void testInnerTypeLastCompactSourceFile() throws Exception {
+ 146:         final String[] expected = {
+ 147:             "12:1: " + getCheckMessage(MSG_KEY),
+ 148:         };
+ 149:         verifyWithInlineConfigParser(
+ 150:                 getNonCompilablePath("compact/InputInnerTypeLastCompactSourceFile.java"), expected);
+ 151:     }
+ 152: 
+ 153:     @Test
+ 154:     public void testInnerTypeLastCompactSourceFileNested() throws Exception {
+ 155:         final String[] expected = {
+ 156:             "15:5: " + getCheckMessage(MSG_KEY),
+ 157:         };
+ 158:         verifyWithInlineConfigParser(
+ 159:                 getNonCompilablePath("compact/InputInnerTypeLastCompactSourceFileNested.java"),
+ 160:                 expected);
+ 161:     }
+ 162: 
+ 163:     @Test
+ 164:     public void testInnerTypeLastEmpty() throws Exception {
+ 165:         final String[] expected = CommonUtil.EMPTY_STRING_ARRAY;
+ 166:         verifyWithInlineConfigParser(
+ 167:                 getNonCompilablePath("InputInnerTypeLastEmpty.java"), expected);
+ 168:     }
  169: }
```

**The reviewer's comment:**

> The two tests above read their inputs from the `compact/` subdirectory, but this one reads from the parent non-compilable directory. Is the empty input unrelated to compact source files? If it is part of the same scenario it would be easier to follow next to the others.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 9. `claude-code-subagent__opus__mockito__mockito__2807__unmatched_model__4`

**Arm:** `opus`  •  **File:** `src/main/java/org/mockito/ArgumentMatchers.java`  •  **comment on line 786**  •  [PR #2807](https://github.com/mockito/mockito/pull/2807)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  689:      *
  690:      * <p>
  691:      * See examples in javadoc for {@link ArgumentMatchers} class
  692:      * </p>
  693:      *
  694:      * @return <code>null</code>.
  695:      * @see #isNotNull()
  696:      */
  697:     public static <T> T isNull() {
  698:         reportMatcher(Null.NULL);
  699:         return null;
  700:     }
  701: 
+ 702:     /**
+ 703:      * <code>null</code> argument.
+ 704:      *
+ 705:      * <p>
+ 706:      * See examples in javadoc for {@link ArgumentMatchers} class
+ 707:      * </p>
+ 708:      *
+ 709:      * @param type the type of the argument being matched.
+ 710:      * @return <code>null</code>.
+ 711:      * @see #isNotNull(Class)
+ 712:      */
+ 713:     public static <T> T isNull(Class<T> type) {
+ 714:         reportMatcher(new Null(type));
+ 715:         return null;
+ 716:     }
+ 717: 
  718:     /**
  719:      * Not <code>null</code> argument.
  720:      *
  721:      * <p>
  722:      * Alias to {@link ArgumentMatchers#isNotNull()}
  723:      * </p>
  724:      *
  725:      * <p>
  726:      * See examples in javadoc for {@link ArgumentMatchers} class
  727:      * </p>
  728:      *
  729:      * @return <code>null</code>.
  730:      */
  731:     public static <T> T notNull() {
  732:         reportMatcher(NotNull.NOT_NULL);
  733:         return null;
  734:     }
  735: 
+ 736:     /**
+ 737:      * Not <code>null</code> argument.
+ 738:      *
+ 739:      * <p>
+ 740:      * Alias to {@link ArgumentMatchers#isNotNull()}
+ 741:      * </p>
+ 742:      *
+ 743:      * <p>
+ 744:      * See examples in javadoc for {@link ArgumentMatchers} class
+ 745:      * </p>
+ 746:      *
+ 747:      * @param type the type of the argument being matched.
+ 748:      * @return <code>null</code>.
+ 749:      */
+ 750:     public static <T> T notNull(Class<T> type) {
+ 751:         reportMatcher(new NotNull(type));
+ 752:         return null;
+ 753:     }
+ 754: 
  755:     /**
  756:      * Not <code>null</code> argument.
  757:      *
  758:      * <p>
  759:      * Alias to {@link ArgumentMatchers#notNull()}
  760:      * </p>
  761:      *
  762:      * <p>
  763:      * See examples in javadoc for {@link ArgumentMatchers} class
  764:      * </p>
  765:      *
  766:      * @return <code>null</code>.
  767:      * @see #isNull()
  768:      */
  769:     public static <T> T isNotNull() {
  770:         return notNull();
  771:     }
  772: 
+ 773:     /**
+ 774:      * Not <code>null</code> argument.
+ 775:      *
+ 776:      * <p>
+ 777:      * Alias to {@link ArgumentMatchers#notNull(Class)}
+ 778:      * </p>
+ 779:      *
+ 780:      * <p>
+ 781:      * See examples in javadoc for {@link ArgumentMatchers} class
+ 782:      * </p>
+ 783:      *
+ 784:      * @param type the type of the argument being matched.
+ 785:      * @return <code>null</code>.
+ 786:      * @see #isNull()
+ 787:      */
+ 788:     public static <T> T isNotNull(Class<T> type) {
+ 789:         return notNull(type);
+ 790:     }
+ 791: 
  792:     /**
  793:      * Argument that is either <code>null</code> or of the given type.
  794:      *
  795:      * <p>
  796:      * See examples in javadoc for {@link ArgumentMatchers} class
  797:      * </p>
  798:      *
  799:      * @param clazz Type to avoid casting
  800:      * @return <code>null</code>.
  801:      */
  802:     public static <T> T nullable(Class<T> clazz) {
  803:         AdditionalMatchers.or(isNull(), isA(clazz));
  804:         return Primitives.defaultValue(clazz);
```

**The reviewer's comment:**

> @see should point at the matching overload isNull(Class) rather than the no-arg isNull().

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 10. `claude-code-subagent__opus__junit-team__junit5__5042__unmatched_model__24`

**Arm:** `opus`  •  **File:** `platform-tooling-support-tests/src/test/java/platform/tooling/support/tests/JUnitStartTests.java`  •  **comment on line 106**  •  [PR #5042](https://github.com/junit-team/junit5/pull/5042)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2:  * Copyright 2015-2025 the original author or authors.
+ 3:  *
+ 4:  * All rights reserved. This program and the accompanying materials are
+ 5:  * made available under the terms of the Eclipse Public License v2.0 which
+ 6:  * accompanies this distribution and is available at
+ 7:  *
+ 8:  * https://www.eclipse.org/legal/epl-v20.html
+ 9:  */
+ 10: 
+ 11: package platform.tooling.support.tests;
+ 12: 
+ 13: import static org.junit.jupiter.api.Assertions.assertEquals;
+ 14: import static org.junit.jupiter.api.Assertions.assertTrue;
+ 15: import static platform.tooling.support.tests.Projects.copyToWorkspace;
+ 16: 
+ 17: import java.nio.file.Files;
+ 18: import java.nio.file.Path;
+ 19: 
+ 20: import org.junit.jupiter.api.BeforeAll;
+ 21: import org.junit.jupiter.api.Test;
+ 22: import org.junit.jupiter.api.condition.EnabledOnJre;
+ 23: import org.junit.jupiter.api.condition.JRE;
+ 24: import org.junit.jupiter.api.io.TempDir;
+ 25: import org.junit.platform.tests.process.OutputFiles;
+ 26: 
+ 27: import platform.tooling.support.Helper;
+ 28: import platform.tooling.support.MavenRepo;
+ 29: import platform.tooling.support.ProcessStarters;
+ 30: import platform.tooling.support.ThirdPartyJars;
+ 31: 
+ 32: /**
+ 33:  * @since 6.1
+ 34:  */
+ 35: class JUnitStartTests {
+ 36: 
+ 37: 	@TempDir
+ 38: 	static Path workspace;
+ 39: 
+ 40: 	@BeforeAll
+ 41: 	static void prepareLocalLibraryDirectoryWithJUnitModules() throws Exception {
+ 42: 		copyToWorkspace(Projects.JUNIT_start, workspace);
+ 43: 		var lib = workspace.resolve("lib");
+ 44: 		try {
+ 45: 			Files.createDirectories(lib);
+ 46: 			try (var directoryStream = Files.newDirectoryStream(lib, "*.jar")) {
+ 47: 				for (Path jarFile : directoryStream) {
+ 48: 					Files.delete(jarFile);
+ 49: 				}
+ 50: 			}
+ 51: 			for (var module : Helper.loadModuleDirectoryNames()) {
+ 52: 				if (module.startsWith("junit-platform") || module.startsWith("junit-jupiter")
+ 53: 						|| module.equals("junit-start")) {
+ 54: 					if (module.equals("junit-jupiter-migrationsupport"))
+ 55: 						continue;
+ 56: 					if (module.startsWith("junit-platform-suite"))
+ 57: 						continue;
+ 58: 					if (module.equals("junit-platform-testkit"))
+ 59: 						continue;
+ 60: 					var jar = MavenRepo.jar(module);
+ 61: 					Files.copy(jar, lib.resolve(module + ".jar"));
+ 62: 				}
+ 63: 			}
+ 64: 			ThirdPartyJars.copy(lib, "org.apiguardian", "apiguardian-api");
+ 65: 			ThirdPartyJars.copy(lib, "org.jspecify", "jspecify");
+ 66: 			ThirdPartyJars.copy(lib, "org.opentest4j", "opentest4j");
+ 67: 			ThirdPartyJars.copy(lib, "org.opentest4j.reporting", "open-test-reporting-tooling-spi");
+ 68: 		}
+ 69: 		catch (Exception e) {
+ 70: 			throw new AssertionError("Preparing local library folder failed", e);
+ 71: 		}
+ 72: 	}
+ 73: 
+ 74: 	@Test
+ 75: 	@EnabledOnJre(JRE.JAVA_25)
+ 76: 	void junitRun(@FilePrefix("junit-run") OutputFiles outputFiles) throws Exception {
+ 77: 		var result = ProcessStarters.java() //
+ 78: 				.workingDir(workspace) //
+ 79: 				.addArguments("--module-path", "lib") // relative to workspace
+ 80: 				.addArguments("--add-modules", "org.junit.start") // configure root module
+ 81: 				.addArguments("compact/JUnitRun.java") // leverage Java's source mode
+ 82: 				.redirectOutput(outputFiles) //
+ 83: 				.startAndWait();
+ 84: 
+ 85: 		assertEquals(0, result.exitCode());
+ 86: 		assertTrue(result.stdOut().contains("addition()"), result.stdOut());
+ 87: 	}
+ 88: 
+ 89: 	@Test
+ 90: 	@EnabledOnJre(JRE.JAVA_25)
+ 91: 	void junitRunClass(@FilePrefix("junit-run-class") OutputFiles outputFiles) throws Exception {
+ 92: 		var result = ProcessStarters.java() //
+ 93: 				.workingDir(workspace) //
+ 94: 				.addArguments("--module-path", "lib") // relative to workspace
+ 95: 				.addArguments("--add-modules", "org.junit.start") // configure root module
+ 96: 				.addArguments("compact/JUnitRunClass.java") // leverage Java's source mode
+ 97: 				.redirectOutput(outputFiles) //
+ 98: 				.startAndWait();
+ 99: 
+ 100: 		assertEquals(0, result.exitCode());
+ 101: 		assertTrue(result.stdOut().contains("substraction()"), result.stdOut());
+ 102: 	}
+ 103: 
+ 104: 	@Test
+ 105: 	@EnabledOnJre(JRE.JAVA_25)
+ 106: 	void junitRunModule(@FilePrefix("junit-run-Module") OutputFiles outputFiles) throws Exception {
+ 107: 		var result = ProcessStarters.java() //
+ 108: 				.workingDir(workspace) //
+ 109: 				.putEnvironment("NO_COLOR", "1") // --disable-ansi-colors
+ 110: 				.addArguments("--module-path", "lib") // relative to workspace
+ 111: 				.addArguments("modular/p/JUnitRunModule.java") // leverage Java's source mode
+ 112: 				.redirectOutput(outputFiles) //
+ 113: 				.startAndWait();
+ 114: 
+ 115: 		assertEquals(0, result.exitCode());
+ 116: 		assertTrue(result.stdOut().contains("multiplication()"), result.stdOut());
+ 117: 	}
+ 118: 
+ 119: }
```

**The reviewer's comment:**

> File prefix `"junit-run-Module"` is inconsistently capitalized compared to `"junit-run"` and `"junit-run-class"`; use `"junit-run-module"`.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 11. `claude-code-subagent__opus__checkstyle__checkstyle__20604__unmatched_model__1`

**Arm:** `opus`  •  **File:** `src/test/java/com/puppycrawl/tools/checkstyle/internal/XdocsExamplesAstConsistencyTest.java`  •  **comment on line 193**  •  [PR #20604](https://github.com/checkstyle/checkstyle/pull/20604)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  89:  * <p>Block comments used as {@code ok} or {@code violation} markers
  90:  * (e.g. {@code /* ok, allowMissingReturnTag is true *}{@code /}) are forbidden;
  91:  * use single-line {@code //} comments instead. The
  92:  * {@link #testNoBlockCommentMarkers()} test enforces this.
  93:  *
  94:  */
  95: public class XdocsExamplesAstConsistencyTest {
  96: 
  97:     private static final Path XDOCS_ROOT = Path.of(
  98:             "src/xdocs-examples/resources/com/puppycrawl/tools/checkstyle"
  99:     );
  100:     private static final String XDOC_START_MARKER = "// xdoc section -- start";
  101:     private static final String XDOC_END_MARKER = "// xdoc section -- end";
+ 102:     private static final Pattern BLOCK_COMMENT_PATTERN = Pattern.compile("(?s)/\\*.*?\\*/");
  103: 
  104:     /**
  105:      * Examples that cannot be parsed as valid Java.
  106:      * These files are intentionally non-compilable for documentation purposes.
  107:      *
  108:      */
  109:     private static final Set<String> UNPARSEABLE_EXAMPLES = Set.of(
  110:             "checks/regexp/regexponfilename/Example1",
  111:             "checks/translation/Example1",
  112:             "filters/suppressionxpathsinglefilter/Example14"
  113:     );
  114: 
+ 115:     /**
+ 116:      * Cache for module property counts to avoid repeated, expensive reflective lookups
+ 117:      * during test execution.
+ 118:      */
+ 119:     private static final ConcurrentMap<String, Integer> PROPERTY_COUNT_CACHE =
+ 120:         new ConcurrentHashMap<>();
+ 121: 
+ 122:     /**
+ 123:      * Cache mapping a lower-cased xdocs directory name (e.g. {@code declarationorder}) to
+ 124:      * the check's simple class name (e.g. {@code DeclarationOrderCheck}), built once from
+ 125:      * the full list of checkstyle module classes. Avoids repeated classpath scans.
+ 126:      */
+ 127:     private static final ConcurrentMap<String, String> MODULE_SIMPLE_NAME_CACHE =
+ 128:         buildModuleSimpleNameIndex();
+ 129: 
+ 130:     /**
+ 131:      * Modules where the example-count-matches-property-count validation should be skipped,
+ 132:      * e.g. because the directory intentionally demonstrates use-cases rather than a strict
+ 133:      * one-example-per-property mapping.
+ 134:      */
+ 135:     private static final Set<String> EXAMPLE_COUNT_SUPPRESSED_MODULES = Set.of(
+ 136:         // until https://github.com/checkstyle/checkstyle/issues/20625
+ 137:         "checks/annotation/annotationlocation",
+ 138:         "checks/annotation/suppresswarnings",
+ 139:         "checks/blocks/leftcurly",
+ 140:         "checks/coding/illegaltokentext",
+ 141:         "checks/coding/magicnumber",
+ 142:         "checks/descendanttoken",
+ 143:         "checks/imports/importcontrol",
+ 144:         "checks/imports/unusedimports",
+ 145:         "checks/javadoc/atclauseorder",
+ 146:         "checks/javadoc/javadocblocktaglocation",
+ 147:         "checks/javadoc/javadocmethod",
+ 148:         "checks/javadoc/javadocparagraph",
+ 149:         "checks/javadoc/javadoctype",
+ 150:         "checks/javadoc/javadocvariable",
+ 151:         "checks/javadoc/missingjavadocmethod",
+ 152:         "checks/javadoc/missingjavadoctype",
+ 153:         "checks/javadoc/nonemptyatclausedescription",
+ 154:         "checks/javadoc/summaryjavadoc",
+ 155:         "checks/javadoc/writetag",
+ 156:         "checks/metrics/classdataabstractioncoupling",
+ 157:         "checks/metrics/cyclomaticcomplexity",
+ 158:         "checks/modifier/interfacememberimpliedmodifier",
+ 159:         "checks/naming/abbreviationaswordinname",
+ 160:         "checks/naming/constantname",
+ 161:         "checks/naming/illegalidentifiername",
+ 162:         "checks/naming/localfinalvariablename",
+ 163:         "checks/naming/membername",
+ 164:         "checks/naming/methodname",
+ 165:         "checks/naming/staticvariablename",
+ 166:         "checks/naming/typename",
+ 167:         "checks/regexp/regexp",
+ 168:         "checks/regexp/regexpmultiline",
+ 169:         "checks/regexp/regexponfilename",
+ 170:         "checks/regexp/regexpsingleline",
+ 171:         "checks/regexp/regexpsinglelinejava",
+ 172:         "checks/sizes/methodcount",
+ 173:         "checks/sizes/methodlength",
+ 174:         "checks/sizes/parameternumber",
+ 175:         "checks/translation",
+ 176:         "checks/whitespace/methodparampad",
+ 177:         "checks/whitespace/nowhitespaceafter",
+ 178:         "checks/whitespace/operatorwrap",
+ 179:         "checks/whitespace/parenpad",
+ 180:         "checks/whitespace/separatorwrap",
+ 181:         "filters/suppressioncommentfilter",
+ 182:         "filters/suppressionsinglefilter",
+ 183:         "filters/suppressionxpathfilter",
+ 184:         "filters/suppressionxpathsinglefilter",
+ 185:         "filters/suppresswithnearbycommentfilter",
+ 186:         "filters/suppresswithnearbytextfilter"
+ 187:     );
+ 188: 
+ 189:     /**
+ 190:      * Modules where the every-property-has-an-example validation should be skipped,
+ 191:      * pending individual fixes.
+ 192:      */
+ 193:     private static final Set<String> EXAMPLE_PROPERTY_COVERAGE_SUPPRESSED_MODULES = Set.of(
+ 194:             // until https://github.com/checkstyle/checkstyle/issues/20624
+ 195:             "checks/imports/illegalimport",
+ 196:             "checks/imports/unusedimports",
+ 197:             "checks/javadoc/atclauseorder",
+ 198:             "checks/javadoc/javadocblocktaglocation",
+ 199:             "checks/javadoc/javadocmethod",
+ 200:             "checks/javadoc/javadocparagraph",
+ 201:             "checks/javadoc/javadoctype",
+ 202:             "checks/javadoc/javadocvariable",
+ 203:             "checks/javadoc/missingjavadocmethod",
+ 204:             "checks/javadoc/missingjavadoctype",
+ 205:             "checks/javadoc/nonemptyatclausedescription",
+ 206:             "checks/javadoc/summaryjavadoc",
+ 207:             "checks/lineending",
+ 208:             "checks/metrics/classdataabstractioncoupling",
+ 209:             "checks/modifier/classmemberimpliedmodifier",
+ 210:             "checks/naming/illegalidentifiername",
+ 211:             "checks/newlineatendoffile",
+ 212:             "checks/regexp/regexpmultiline",
+ 213:             "checks/regexp/regexponfilename",
+ 214:             "checks/sizes/methodcount",
+ 215:             "filters/suppressionsinglefilter",
+ 216:             "filters/suppresswithnearbycommentfilter"
+ 217:     );
+ 218: 
  219:     /**
  220:      * Examples that have independent code structure and should not be compared.
  221:      * These represent different use cases or configurations with different code.
  222:      *
  223:      * <p>Format: "directory/ExampleN" where the example has unique code.
  224:      *
  225:      * <p>Until: <a href="https://github.com/checkstyle/checkstyle/issues/19891">...</a>
  226:      */
  227:     private static final Set<String> SUPPRESSED_EXAMPLES = Set.of(
  228:             // Note: customImport/ImportOrder changes import group ORDER affecting AST structure
  229:             "checks/imports/customimportorder/Example10",
  230:             "checks/imports/customimportorder/Example11",
  231:             "checks/imports/customimportorder/Example12",
```

**The reviewer's comment:**

> The entries of this `Set.of(...)` are indented with 12 spaces while the entries of the set declared just above use 8. Pick one continuation indent for both so the two adjacent constants read consistently.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 12. `claude-code-subagent__opus__checkstyle__checkstyle__20600__unmatched_model__8`

**Arm:** `opus`  •  **File:** `src/site/xdoc/checks/misc/multilinecommentleadingasteriskpresence.xml`  •  **comment on line 43**  •  [PR #20600](https://github.com/checkstyle/checkstyle/pull/20600)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: <?xml version="1.0" encoding="UTF-8"?>
+ 2: <document xmlns="http://maven.apache.org/XDOC/2.0"
+ 3:   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
+ 4:   xsi:schemaLocation="http://maven.apache.org/XDOC/2.0 https://maven.apache.org/xsd/xdoc-2.0.xsd">
+ 5:   <head>
+ 6:     <title>MultilineCommentLeadingAsteriskPresence</title>
+ 7:   </head>
+ 8:   <body>
+ 9:     <section name="MultilineCommentLeadingAsteriskPresence">
+ 10:       <p>Since Checkstyle 13.8.0</p>
+ 11:       <subsection name="Description" id="MultilineCommentLeadingAsteriskPresence_Description">
+ 12:         <div>
+ 13:           Checks if the multi-line bock comments has
+ 14:           <a href="https://www.oracle.com/java/technologies/javase/codeconventions-comments.html">
+ 15:           leading asterisks</a> on each line.
+ 16:         </div>
+ 17: 
+ 18:         <p>
+ 19:           Every line in multi-line comment should have leading asterisk including blank line.
+ 20:         </p>
+ 21:       </subsection>
+ 22: 
+ 23:       <subsection name="Examples" id="MultilineCommentLeadingAsteriskPresence_Examples">
+ 24:         <p id="Example1-config">To configure the check:</p>
+ 25:         <div class="wrapper"><pre class="prettyprint"><code class="language-xml">
+ 26: &lt;module name="Checker"&gt;
+ 27:   &lt;module name="TreeWalker"&gt;
+ 28:     &lt;module name="MultilineCommentLeadingAsteriskPresence"/&gt;
+ 29:   &lt;/module&gt;
+ 30: &lt;/module&gt;
+ 31: </code></pre></div>
+ 32: 
+ 33:         <p id="Example1-code">Example:</p>
+ 34:         <div class="wrapper"><pre class="prettyprint"><code class="language-java">
+ 35: public class Example1 {
+ 36: 
+ 37:   /*
+ 38:    * Line has leading asterisk.
+ 39:    */
+ 40:   void foo() {}
+ 41: 
+ 42:   // violation 2 lines below 'Multiline comment should start with leading asterisk'
+ 43:   /* Line with leading asterisk
+ 44:      Line with leading asterisk
+ 45:   */
+ 46:   void bar() {}
+ 47: 
+ 48:   /* Single line comment */
+ 49:   void method() {}
+ 50: 
+ 51: }
+ 52: </code></pre></div>
+ 53:       </subsection>
+ 54: 
+ 55:       <subsection name="Example of Usage"
+ 56:         id="MultilineCommentLeadingAsteriskPresence_Example_of_Usage">
+ 57:         <ul>
+ 58:           <li>
+ 59:            <a href="https://github.com/search?q=path%3Aconfig%20path%3A**%2Fcheckstyle-checks.xml+repo%3Acheckstyle%2Fcheckstyle+MultilineCommentLeadingAsteriskPresence">
+ 60:            Checkstyle Style
+ 61:             </a>
+ 62:           </li>
+ 63:         </ul>
+ 64:       </subsection>
+ 65: 
+ 66:       <subsection name="Violation Messages"
+ 67:         id="MultilineCommentLeadingAsteriskPresence_Violation_Messages">
+ 68:         <ul>
+ 69:           <li>
+ 70:             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22multiline.comment.missing.asterisk%22">
+ 71:               multiline.comment.missing.asterisk
+ 72:             </a>
+ 73:           </li>
+ 74:         </ul>
+ 75:         <p>
+ 76:           All messages can be customized if the default message doesn't suit you.
+ 77:           Please <a href="../../config.html#Custom_messages">see the documentation</a>
+ 78:           to learn how to.
+ 79:         </p>
+ 80:       </subsection>
+ 81: 
+ 82: <subsection name="Fully Qualified Name"
+ 83:                 id="MultilineCommentLeadingAsteriskPresence_Fully_Qualified_Name">
+ 84:     <p>com.puppycrawl.tools.checkstyle.checks.MultilineCommentLeadingAsteriskPresenceCheck</p>
+ 85:     <p>
+ 86:       Use this fully qualified class name in configuration when an exact class reference is
+ 87:       required.
+ 88:     </p>
+ 89:   </subsection>
+ 90: 
+ 91:       <subsection name="Parent Module"
+ 92:         id="MultilineCommentLeadingAsteriskPresence_Parent_Module">
+ 93:         <p>
+ 94:           <a href="../../config.html#TreeWalker">TreeWalker</a>
+ 95:         </p>
+ 96:       </subsection>
+ 97:     </section>
+ 98:   </body>
+ 99: </document>
```

**The reviewer's comment:**

> The example is self-contradictory: both lines of this comment are labelled "Line with leading asterisk", but neither actually has a leading asterisk - that is precisely why the violation is reported. The text should say "without leading asterisk".

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 13. `claude-code-subagent__opus__mockito__mockito__2603__unmatched_model__1`

**Arm:** `opus`  •  **File:** `subprojects/junit-jupiter/src/test/java/org/mockitousage/InjectMocksTest.java`  •  **comment on line 35**  •  [PR #2603](https://github.com/mockito/mockito/pull/2603)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2:  * Copyright (c) 2018 Mockito contributors
+ 3:  * This program is made available under the terms of the MIT License.
+ 4:  */
+ 5: package org.mockitousage;
+ 6: 
+ 7: import org.junit.jupiter.api.Test;
+ 8: import org.junit.jupiter.api.extension.ExtendWith;
+ 9: import org.mockito.InjectMocks;
+ 10: import org.mockito.Mock;
+ 11: import org.mockito.junit.jupiter.MockitoExtension;
+ 12: 
+ 13: import static org.assertj.core.api.Assertions.assertThat;
+ 14: 
+ 15: class ToBeMockedInTestSuperClass{
+ 16:     int identifier;
+ 17: 
+ 18:     public ToBeMockedInTestSuperClass(int identifier) {
+ 19:         this.identifier = identifier;
+ 20:     }
+ 21: }
+ 22: 
+ 23: class ToBeMocked{
+ 24:     int identifier;
+ 25: 
+ 26:     public ToBeMocked(int identifier) {
+ 27:         this.identifier = identifier;
+ 28:     }
+ 29: }
+ 30: 
+ 31: class TestClassToBeInitiatedViaConstructorInSuperClass {
+ 32:     ToBeMockedInTestSuperClass toBeMockedInTestSuperClass;
+ 33: 
+ 34:     public TestClassToBeInitiatedViaConstructorInSuperClass(ToBeMockedInTestSuperClass toBeMockedInTestSuperClass) {
+ 35:         assert toBeMockedInTestSuperClass != null;
+ 36:         this.toBeMockedInTestSuperClass = new ToBeMockedInTestSuperClass(42);
+ 37:     }
+ 38: }
+ 39: 
+ 40: class TestClassToBeInitiatedViaConstructor{
+ 41:     ToBeMockedInTestSuperClass toBeMockedInTestSuperClass;
+ 42:     ToBeMocked toBeMocked;
+ 43: 
+ 44:     public TestClassToBeInitiatedViaConstructor(ToBeMocked toBeMocked, ToBeMockedInTestSuperClass toBeMockedInTestSuperClass) {
+ 45:         assert toBeMocked != null;
+ 46:         assert toBeMockedInTestSuperClass != null;
+ 47:         this.toBeMocked = new ToBeMocked(42);
+ 48:         this.toBeMockedInTestSuperClass = new ToBeMockedInTestSuperClass(42);
+ 49:     }
+ 50: }
+ 51: 
+ 52: class SuperTestClass {
+ 53:     @Mock
+ 54:     ToBeMockedInTestSuperClass toBeMockedInTestSuperClass;
+ 55: 
+ 56:     @InjectMocks
+ 57:     TestClassToBeInitiatedViaConstructorInSuperClass testClassToBeInitiatedViaConstructorInSuperClass;
+ 58: 
+ 59: }
+ 60: 
+ 61: @ExtendWith(MockitoExtension.class)
+ 62: class InjectMocksTest extends SuperTestClass {
+ 63: 
+ 64:     @Mock
+ 65:     ToBeMocked toBeMocked;
+ 66: 
+ 67:     @InjectMocks
+ 68:     TestClassToBeInitiatedViaConstructor testClassToBeInitiatedViaConstructor;
+ 69: 
+ 70:     /**
+ 71:      * Checks that {@link #testClassToBeInitiatedViaConstructor} holds instances that have identifier 42.
+ 72:      * It being 42 is proof that constructor injection was used over field injection.
+ 73:      */
+ 74:     @Test
+ 75:     void given_instanceToBeInitializedByMockito_when_mocksRequestedByConstructorAreInTestAndSuperClass_should_useConstructorInjection() {
+ 76:         assertThat(testClassToBeInitiatedViaConstructor)
+ 77:             .extracting(
+ 78:                 testInstance-> testInstance.toBeMocked.identifier,
+ 79:                 testInstance-> testInstance.toBeMockedInTestSuperClass.identifier
+ 80:             )
+ 81:             .containsExactly(
+ 82:                 42,
+ 83:                 42
+ 84:             );
+ 85:     }
+ 86: 
+ 87:     /**
+ 88:      * Checks that {@link #testClassToBeInitiatedViaConstructorInSuperClass} holds instances that have identifier 42.
+ 89:      * It being 42 is proof that constructor injection was used over field injection.
+ 90:      */
+ 91:     @Test
+ 92:     public void given_instanceInSuperClassToBeInitializedByMockito_when_mocksRequestedAreInSuperClass_should_useConstructorInjection(){
+ 93:         assertThat(testClassToBeInitiatedViaConstructorInSuperClass)
+ 94:             .extracting(yetAnotherClas1 -> yetAnotherClas1.toBeMockedInTestSuperClass.identifier)
+ 95:             .isEqualTo(42);
+ 96:     }
+ 97: 
+ 98: }
```

**The reviewer's comment:**

> The verification that Mockito passed a mock into the constructor relies on `assert`, which is a no-op unless assertions are enabled (`-ea`). If they are ever off, this constructor silently accepts `null` and the test still passes. Use an explicit check (e.g. `Objects.requireNonNull` or an AssertJ assertion in the test) instead.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 14. `anthropic__claude-sonnet-5__junit-team__junit5__5042__unmatched_model__8`

**Arm:** `sonnet`  •  **File:** `platform-tooling-support-tests/src/test/java/platform/tooling/support/tests/Projects.java`  •  **comment on line 24**  •  [PR #5042](https://github.com/junit-team/junit5/pull/5042)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  11: package platform.tooling.support.tests;
  12: 
  13: import java.io.IOException;
  14: import java.nio.file.Path;
  15: 
  16: import org.apache.commons.io.file.PathUtils;
  17: 
  18: public class Projects {
  19: 
  20: 	public static final String GRAALVM_STARTER = "graalvm-starter";
  21: 	public static final String GRADLE_KOTLIN_EXTENSIONS = "gradle-kotlin-extensions";
  22: 	public static final String GRADLE_MISSING_ENGINE = "gradle-missing-engine";
  23: 	public static final String JAR_DESCRIBE_MODULE = "jar-describe-module";
+ 24: 	public static final String JUNIT_start = "junit-start";
  25: 	public static final String JUPITER_STARTER = "jupiter-starter";
  26: 	public static final String KOTLIN_COROUTINES = "kotlin-coroutines";
  27: 	public static final String MAVEN_SUREFIRE_COMPATIBILITY = "maven-surefire-compatibility";
  28: 	public static final String REFLECTION_TESTS = "reflection-tests";
  29: 	public static final String STANDALONE = "standalone";
  30: 	public static final String VINTAGE = "vintage";
  31: 
  32: 	private Projects() {
  33: 	}
  34: 
  35: 	static Path copyToWorkspace(String project, Path workspace) throws IOException {
  36: 		PathUtils.copyDirectory(getSourceDirectory(project), workspace);
  37: 		return workspace;
```

**The reviewer's comment:**

> Constant name JUNIT_start doesn't follow the ALL_CAPS naming convention used by every other constant in this class (e.g. JAR_DESCRIBE_MODULE, JUPITER_STARTER, KOTLIN_COROUTINES). Should be JUNIT_START.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 15. `claude-code-subagent__opus__junit-team__junit5__5042__unmatched_model__17`

**Arm:** `opus`  •  **File:** `platform-tooling-support-tests/projects/junit-start/compact/JUnitRunClass.java`  •  **comment on line 18**  •  [PR #5042](https://github.com/junit-team/junit5/pull/5042)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2:  * Copyright 2015-2025 the original author or authors.
+ 3:  *
+ 4:  * All rights reserved. This program and the accompanying materials are
+ 5:  * made available under the terms of the Eclipse Public License v2.0 which
+ 6:  * accompanies this distribution and is available at
+ 7:  *
+ 8:  * https://www.eclipse.org/legal/epl-v20.html
+ 9:  */
+ 10: 
+ 11: import module org.junit.start;
+ 12: 
+ 13: void main() {
+ 14: 	JUnit.run(getClass());
+ 15: }
+ 16: 
+ 17: @Test
+ 18: void substraction() {
+ 19: 	Assertions.assertEquals(2, 3 - 1, "Subtraction error detected!");
+ 20: }
```

**The reviewer's comment:**

> Typo in the test method name: `substraction` should be `subtraction` (the failure message on the next line spells it correctly). Test method names show up verbatim in reports, so the misspelling is user-visible.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 16. `claude-code-subagent__opus__checkstyle__checkstyle__20600__unmatched_model__17`

**Arm:** `opus`  •  **File:** `src/test/resources/com/puppycrawl/tools/checkstyle/checks/multilinecommentleadingasteriskpresence/InputMultilineCommentLeadingAsteriskPresenceCorrect.java`  •  **comment on line 5**  •  [PR #20600](https://github.com/checkstyle/checkstyle/pull/20600)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2: MultilineCommentLeadingAsteriskPresence
+ 3: 
+ 4: */
+ 5: // violation 3 lines above 'Multiline comment should start with leading asterisk'
+ 6: // violation 3 lines above 'Multiline comment should start with leading asterisk'
+ 7: 
+ 8: package com.puppycrawl.tools.checkstyle.checks.multilinecommentleadingasteriskpresence;
+ 9: 
+ 10: public class InputMultilineCommentLeadingAsteriskPresenceCorrect {
+ 11: 
+ 12:     /*
+ 13:      * This method does nothing.
+ 14:      */
+ 15:     void method(int... a) {
+ 16:         return;
+ 17:     }
+ 18: 
+ 19:     /* Line 1
+ 20:      * Line 2
+ 21:      * Line 3
+ 22:      * Line 4 */
+ 23:     void foo() {}
+ 24: 
+ 25:     /* This method is empty. */
+ 26:     void foo1() {}
+ 27: 
+ 28:     /* Line 1
+ 29:      *
+ 30:      * Line 3
+ 31:      *
+ 32:      * Line 4
+ 33:      */
+ 34:     void bar() {}
+ 35: }
```

**The reviewer's comment:**

> This input is named `...Correct` but still declares two expected violations, both coming from the config header block at lines 1-4 rather than from the code under test. Is that intended? A file meant to demonstrate correct usage would be clearer if it produced no violations at all.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 17. `anthropic__claude-sonnet-5__junit-team__junit5__5060__unmatched_model__6`

**Arm:** `sonnet`  •  **File:** `junit-platform-engine/src/main/java/org/junit/platform/engine/support/hierarchical/ConcurrentHierarchicalTestExecutorService.java`  •  **comment on line 470**  •  [PR #5060](https://github.com/junit-team/junit5/pull/5060)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2:  * Copyright 2015-2025 the original author or authors.
+ 3:  *
+ 4:  * All rights reserved. This program and the accompanying materials are
+ 5:  * made available under the terms of the Eclipse Public License v2.0 which
+ 6:  * accompanies this distribution and is available at
+ 7:  *
+ 8:  * https://www.eclipse.org/legal/epl-v20.html
+ 9:  */
+ 10: 
+ 11: package org.junit.platform.engine.support.hierarchical;
+ 12: 
+ 13: import static java.util.Objects.requireNonNull;
+ 14: import static java.util.concurrent.CompletableFuture.completedFuture;
+ 15: import static java.util.concurrent.TimeUnit.SECONDS;
+ 16: import static org.apiguardian.api.API.Status.EXPERIMENTAL;
+ 17: import static org.junit.platform.commons.util.ExceptionUtils.throwAsUncheckedException;
+ 18: import static org.junit.platform.engine.support.hierarchical.ExclusiveResource.GLOBAL_READ_WRITE;
+ 19: import static org.junit.platform.engine.support.hierarchical.Node.ExecutionMode.SAME_THREAD;
+ 20: 
+ 21: import java.util.ArrayList;
+ 22: import java.util.List;
+ 23: import java.util.Queue;
+ 24: import java.util.concurrent.Callable;
+ 25: import java.util.concurrent.CompletableFuture;
+ 26: import java.util.concurrent.ExecutorService;
+ 27: import java.util.concurrent.Future;
+ 28: import java.util.concurrent.PriorityBlockingQueue;
+ 29: import java.util.concurrent.RejectedExecutionException;
+ 30: import java.util.concurrent.Semaphore;
+ 31: import java.util.concurrent.SynchronousQueue;
+ 32: import java.util.concurrent.ThreadFactory;
+ 33: import java.util.concurrent.ThreadPoolExecutor;
+ 34: import java.util.concurrent.atomic.AtomicInteger;
+ 35: import java.util.function.Consumer;
+ 36: import java.util.function.Supplier;
+ 37: 
+ 38: import org.apiguardian.api.API;
+ 39: import org.jspecify.annotations.Nullable;
+ 40: import org.junit.platform.commons.logging.Logger;
+ 41: import org.junit.platform.commons.logging.LoggerFactory;
+ 42: import org.junit.platform.commons.util.ClassLoaderUtils;
+ 43: import org.junit.platform.commons.util.Preconditions;
+ 44: import org.junit.platform.engine.ConfigurationParameters;
+ 45: 
+ 46: /**
+ 47:  * @since 6.1
+ 48:  */
+ 49: @API(status = EXPERIMENTAL, since = "6.1")
+ 50: public class ConcurrentHierarchicalTestExecutorService implements HierarchicalTestExecutorService {
+ 51: 
+ 52: 	private static final Logger LOGGER = LoggerFactory.getLogger(ConcurrentHierarchicalTestExecutorService.class);
+ 53: 
+ 54: 	private final WorkQueue workQueue = new WorkQueue();
+ 55: 	private final ExecutorService threadPool;
+ 56: 	private final WorkerLeaseManager workerLeaseManager;
+ 57: 
+ 58: 	public ConcurrentHierarchicalTestExecutorService(ConfigurationParameters configurationParameters) {
+ 59: 		this(DefaultParallelExecutionConfigurationStrategy.toConfiguration(configurationParameters));
+ 60: 	}
+ 61: 
+ 62: 	public ConcurrentHierarchicalTestExecutorService(ParallelExecutionConfiguration configuration) {
+ 63: 		this(configuration, ClassLoaderUtils.getDefaultClassLoader());
+ 64: 	}
+ 65: 
+ 66: 	ConcurrentHierarchicalTestExecutorService(ParallelExecutionConfiguration configuration, ClassLoader classLoader) {
+ 67: 		ThreadFactory threadFactory = new WorkerThreadFactory(classLoader);
+ 68: 		threadPool = new ThreadPoolExecutor(configuration.getCorePoolSize(), configuration.getMaxPoolSize(),
+ 69: 			configuration.getKeepAliveSeconds(), SECONDS, new SynchronousQueue<>(), threadFactory);
+ 70: 		workerLeaseManager = new WorkerLeaseManager(configuration.getParallelism());
+ 71: 		LOGGER.trace(() -> "initialized thread pool for parallelism of " + configuration.getParallelism());
+ 72: 	}
+ 73: 
+ 74: 	@Override
+ 75: 	public void close() {
+ 76: 		LOGGER.trace(() -> "shutting down thread pool");
+ 77: 		threadPool.shutdownNow();
+ 78: 	}
+ 79: 
+ 80: 	@Override
+ 81: 	public Future<@Nullable Void> submit(TestTask testTask) {
+ 82: 		LOGGER.trace(() -> "submit: " + testTask);
+ 83: 		if (WorkerThread.get() == null) {
+ 84: 			return enqueue(testTask).future();
+ 85: 		}
+ 86: 		if (testTask.getExecutionMode() == SAME_THREAD) {
+ 87: 			executeTask(testTask);
+ 88: 			return completedFuture(null);
+ 89: 		}
+ 90: 		return new BlockingAwareFuture<@Nullable Void>(enqueue(testTask).future(), WorkerThread.BlockHandler.INSTANCE);
+ 91: 	}
+ 92: 
+ 93: 	@Override
+ 94: 	public void invokeAll(List<? extends TestTask> testTasks) {
+ 95: 		LOGGER.trace(() -> "invokeAll: " + testTasks);
+ 96: 
+ 97: 		var workerThread = WorkerThread.get();
+ 98: 		Preconditions.condition(workerThread != null && workerThread.executor() == this,
+ 99: 			"invokeAll() must not be called from a thread that is not part of this executor");
+ 100: 
+ 101: 		if (testTasks.isEmpty()) {
+ 102: 			return;
+ 103: 		}
+ 104: 
+ 105: 		if (testTasks.size() == 1) {
+ 106: 			executeTask(testTasks.get(0));
+ 107: 			return;
+ 108: 		}
+ 109: 
+ 110: 		List<TestTask> isolatedTasks = new ArrayList<>(testTasks.size());
+ 111: 		List<TestTask> sameThreadTasks = new ArrayList<>(testTasks.size());
+ 112: 		var queueEntries = forkConcurrentChildren(testTasks, isolatedTasks::add, sameThreadTasks::add);
+ 113: 		executeAll(sameThreadTasks);
+ 114: 		var remainingForkedChildren = stealWork(queueEntries);
+ 115: 		waitFor(remainingForkedChildren);
+ 116: 		executeAll(isolatedTasks);
+ 117: 	}
+ 118: 
+ 119: 	private static void waitFor(List<WorkQueue.Entry> children) {
+ 120: 		if (children.isEmpty()) {
+ 121: 			return;
+ 122: 		}
+ 123: 		var future = toCombinedFuture(children);
+ 124: 		try {
+ 125: 			if (future.isDone()) {
+ 126: 				// no need to release worker lease
+ 127: 				future.join();
+ 128: 			}
+ 129: 			else {
+ 130: 				WorkerThread.getOrThrow().runBlocking(() -> {
+ 131: 					LOGGER.trace(() -> "blocking for forked children: " + children);
+ 132: 					return future.join();
+ 133: 				});
+ 134: 			}
+ 135: 		}
+ 136: 		catch (InterruptedException e) {
+ 137: 			Thread.currentThread().interrupt();
+ 138: 		}
+ 139: 	}
+ 140: 
+ 141: 	private WorkQueue.Entry enqueue(TestTask testTask) {
+ 142: 		var entry = workQueue.add(testTask);
+ 143: 		maybeStartWorker();
+ 144: 		return entry;
+ 145: 	}
+ 146: 
+ 147: 	private void maybeStartWorker() {
+ 148: 		if (threadPool.isShutdown() || !workerLeaseManager.isLeaseAvailable() || workQueue.isEmpty()) {
+ 149: 			return;
+ 150: 		}
+ 151: 		try {
+ 152: 			threadPool.execute(() -> {
+ 153: 				LOGGER.trace(() -> "starting worker");
+ 154: 				try {
+ 155: 					WorkerThread.getOrThrow().processQueueEntries();
+ 156: 				}
+ 157: 				finally {
+ 158: 					LOGGER.trace(() -> "stopping worker");
+ 159: 				}
+ 160: 			});
+ 161: 		}
+ 162: 		catch (RejectedExecutionException e) {
+ 163: 			if (threadPool.isShutdown()) {
+ 164: 				return;
+ 165: 			}
+ 166: 			throw e;
+ 167: 		}
+ 168: 	}
+ 169: 
+ 170: 	private static CompletableFuture<?> toCombinedFuture(List<WorkQueue.Entry> entries) {
+ 171: 		if (entries.size() == 1) {
+ 172: 			return entries.get(0).future();
+ 173: 		}
+ 174: 		var futures = entries.stream().map(WorkQueue.Entry::future).toArray(CompletableFuture<?>[]::new);
+ 175: 		return CompletableFuture.allOf(futures);
+ 176: 	}
+ 177: 
+ 178: 	private List<WorkQueue.Entry> stealWork(List<WorkQueue.Entry> queueEntries) {
+ 179: 		if (queueEntries.isEmpty()) {
+ 180: 			return List.of();
+ 181: 		}
+ 182: 		List<WorkQueue.Entry> concurrentlyExecutedChildren = new ArrayList<>(queueEntries.size());
+ 183: 		var iterator = queueEntries.listIterator(queueEntries.size());
+ 184: 		while (iterator.hasPrevious()) {
+ 185: 			var entry = iterator.previous();
+ 186: 			var claimed = workQueue.remove(entry);
+ 187: 			if (claimed) {
+ 188: 				LOGGER.trace(() -> "stole work: " + entry);
+ 189: 				var executed = tryExecute(entry);
+ 190: 				if (!executed) {
+ 191: 					workQueue.add(entry);
+ 192: 					concurrentlyExecutedChildren.add(entry);
+ 193: 				}
+ 194: 			}
+ 195: 			else {
+ 196: 				concurrentlyExecutedChildren.add(entry);
+ 197: 			}
+ 198: 		}
+ 199: 		return concurrentlyExecutedChildren;
+ 200: 	}
+ 201: 
+ 202: 	private List<WorkQueue.Entry> forkConcurrentChildren(List<? extends TestTask> children,
+ 203: 			Consumer<TestTask> isolatedTaskCollector, Consumer<TestTask> sameThreadTaskCollector) {
+ 204: 
+ 205: 		if (children.isEmpty()) {
+ 206: 			return List.of();
+ 207: 		}
+ 208: 		List<WorkQueue.Entry> queueEntries = new ArrayList<>(children.size());
+ 209: 		for (TestTask child : children) {
+ 210: 			if (requiresGlobalReadWriteLock(child)) {
+ 211: 				isolatedTaskCollector.accept(child);
+ 212: 			}
+ 213: 			else if (child.getExecutionMode() == SAME_THREAD) {
+ 214: 				sameThreadTaskCollector.accept(child);
+ 215: 			}
+ 216: 			else {
+ 217: 				queueEntries.add(enqueue(child));
+ 218: 			}
+ 219: 		}
+ 220: 		return queueEntries;
+ 221: 	}
+ 222: 
+ 223: 	private static boolean requiresGlobalReadWriteLock(TestTask testTask) {
+ 224: 		return testTask.getResourceLock().getResources().contains(GLOBAL_READ_WRITE);
+ 225: 	}
+ 226: 
+ 227: 	private void executeAll(List<? extends TestTask> children) {
+ 228: 		if (children.isEmpty()) {
+ 229: 			return;
+ 230: 		}
+ 231: 		LOGGER.trace(() -> "running %d SAME_THREAD children".formatted(children.size()));
+ 232: 		if (children.size() == 1) {
+ 233: 			executeTask(children.get(0));
+ 234: 			return;
+ 235: 		}
+ 236: 		for (var testTask : children) {
+ 237: 			executeTask(testTask);
+ 238: 		}
+ 239: 	}
+ 240: 
+ 241: 	private static boolean tryExecute(WorkQueue.Entry entry) {
+ 242: 		try {
+ 243: 			var executed = tryExecuteTask(entry.task);
+ 244: 			if (executed) {
+ 245: 				entry.future.complete(null);
+ 246: 			}
+ 247: 			return executed;
+ 248: 		}
+ 249: 		catch (Throwable t) {
+ 250: 			entry.future.completeExceptionally(t);
+ 251: 			return true;
+ 252: 		}
+ 253: 	}
+ 254: 
+ 255: 	private void executeEntry(WorkQueue.Entry entry) {
+ 256: 		try {
+ 257: 			executeTask(entry.task);
+ 258: 		}
+ 259: 		catch (Throwable t) {
+ 260: 			entry.future.completeExceptionally(t);
+ 261: 		}
+ 262: 		finally {
+ 263: 			entry.future.complete(null);
+ 264: 		}
+ 265: 	}
+ 266: 
+ 267: 	@SuppressWarnings("try")
+ 268: 	private void executeTask(TestTask testTask) {
+ 269: 		var executed = tryExecuteTask(testTask);
+ 270: 		if (!executed) {
+ 271: 			var resourceLock = testTask.getResourceLock();
+ 272: 			var workerThread = WorkerThread.getOrThrow();
+ 273: 			try (var ignored = workerThread.runBlocking(() -> {
+ 274: 				LOGGER.trace(() -> "blocking for resource lock: " + resourceLock);
+ 275: 				return resourceLock.acquire();
+ 276: 			})) {
+ 277: 				doExecute(testTask);
+ 278: 			}
+ 279: 			catch (InterruptedException ex) {
+ 280: 				Thread.currentThread().interrupt();
+ 281: 			}
+ 282: 		}
+ 283: 	}
+ 284: 
+ 285: 	private static boolean tryExecuteTask(TestTask testTask) {
+ 286: 		var resourceLock = testTask.getResourceLock();
+ 287: 		if (resourceLock.tryAcquire()) {
+ 288: 			try (resourceLock) {
+ 289: 				doExecute(testTask);
+ 290: 				return true;
+ 291: 			}
+ 292: 		}
+ 293: 		return false;
+ 294: 	}
+ 295: 
+ 296: 	private static void doExecute(TestTask testTask) {
+ 297: 		LOGGER.trace(() -> "executing: " + testTask);
+ 298: 		try {
+ 299: 			testTask.execute();
+ 300: 		}
+ 301: 		finally {
+ 302: 			LOGGER.trace(() -> "finished executing: " + testTask);
+ 303: 		}
+ 304: 	}
+ 305: 
+ 306: 	private class WorkerThreadFactory implements ThreadFactory {
+ 307: 
+ 308: 		private static final AtomicInteger POOL_NUMBER = new AtomicInteger(1);
+ 309: 
+ 310: 		private final AtomicInteger threadNumber = new AtomicInteger(1);
+ 311: 		private final int poolNumber;
+ 312: 		private final ClassLoader classLoader;
+ 313: 
+ 314: 		WorkerThreadFactory(ClassLoader classLoader) {
+ 315: 			this.classLoader = classLoader;
+ 316: 			this.poolNumber = POOL_NUMBER.getAndIncrement();
+ 317: 		}
+ 318: 
+ 319: 		@Override
+ 320: 		public Thread newThread(Runnable runnable) {
+ 321: 			var thread = new WorkerThread(runnable,
+ 322: 				"junit-%d-worker-%d".formatted(poolNumber, threadNumber.getAndIncrement()));
+ 323: 			thread.setContextClassLoader(classLoader);
+ 324: 			return thread;
+ 325: 		}
+ 326: 	}
+ 327: 
+ 328: 	private class WorkerThread extends Thread {
+ 329: 
+ 330: 		@Nullable
+ 331: 		WorkerLease workerLease;
+ 332: 
+ 333: 		WorkerThread(Runnable runnable, String name) {
+ 334: 			super(runnable, name);
+ 335: 		}
+ 336: 
+ 337: 		static @Nullable WorkerThread get() {
+ 338: 			if (Thread.currentThread() instanceof WorkerThread workerThread) {
+ 339: 				return workerThread;
+ 340: 			}
+ 341: 			return null;
+ 342: 		}
+ 343: 
+ 344: 		static WorkerThread getOrThrow() {
+ 345: 			var workerThread = get();
+ 346: 			if (workerThread == null) {
+ 347: 				throw new IllegalStateException("Not on a worker thread");
+ 348: 			}
+ 349: 			return workerThread;
+ 350: 		}
+ 351: 
+ 352: 		void processQueueEntries() {
+ 353: 			while (!threadPool.isShutdown()) {
+ 354: 				workerLease = workerLeaseManager.tryAcquire();
+ 355: 				if (workerLease == null) {
+ 356: 					break;
+ 357: 				}
+ 358: 				try {
+ 359: 					var entry = workQueue.poll();
+ 360: 					if (entry == null) {
+ 361: 						break;
+ 362: 					}
+ 363: 					LOGGER.trace(() -> "processing: " + entry.task);
+ 364: 					executeEntry(entry);
+ 365: 				}
+ 366: 				finally {
+ 367: 					workerLease.release();
+ 368: 				}
+ 369: 			}
+ 370: 		}
+ 371: 
+ 372: 		<T> T runBlocking(BlockingAction<T> blockingAction) throws InterruptedException {
+ 373: 			var workerLease = requireNonNull(this.workerLease);
+ 374: 			workerLease.release();
+ 375: 			try {
+ 376: 				return blockingAction.run();
+ 377: 			}
+ 378: 			finally {
+ 379: 				try {
+ 380: 					workerLease.reacquire();
+ 381: 				}
+ 382: 				catch (InterruptedException e) {
+ 383: 					interrupt();
+ 384: 				}
+ 385: 			}
+ 386: 		}
+ 387: 
+ 388: 		interface BlockingAction<T> {
+ 389: 			T run() throws InterruptedException;
+ 390: 		}
+ 391: 
+ 392: 		private ConcurrentHierarchicalTestExecutorService executor() {
+ 393: 			return ConcurrentHierarchicalTestExecutorService.this;
+ 394: 		}
+ 395: 
+ 396: 		private static class BlockHandler implements BlockingAwareFuture.BlockHandler {
+ 397: 
+ 398: 			private static final BlockHandler INSTANCE = new BlockHandler();
+ 399: 
+ 400: 			@Override
+ 401: 			public <T> T handle(Callable<T> callable) throws Exception {
+ 402: 				var workerThread = get();
+ 403: 				if (workerThread == null) {
+ 404: 					return callable.call();
+ 405: 				}
+ 406: 				LOGGER.trace(() -> "blocking for child task");
+ 407: 				return workerThread.runBlocking(() -> {
+ 408: 					try {
+ 409: 						return callable.call();
+ 410: 					}
+ 411: 					catch (Exception ex) {
+ 412: 						throw throwAsUncheckedException(ex);
+ 413: 					}
+ 414: 				});
+ 415: 			}
+ 416: 		}
+ 417: 	}
+ 418: 
+ 419: 	private static class WorkQueue {
+ 420: 
+ 421: 		private final Queue<Entry> queue = new PriorityBlockingQueue<>();
+ 422: 
+ 423: 		Entry add(TestTask task) {
+ 424: 			LOGGER.trace(() -> "forking: " + task);
+ 425: 			int level = task.getTestDescriptor().getUniqueId().getSegments().size();
+ 426: 			return doAdd(new Entry(task, new CompletableFuture<>(), level, 0));
+ 427: 		}
+ 428: 
+ 429: 		void add(Entry entry) {
+ 430: 			LOGGER.trace(() -> "re-enqueuing: " + entry.task);
+ 431: 			doAdd(entry.incrementAttempts());
+ 432: 		}
+ 433: 
+ 434: 		private Entry doAdd(Entry entry) {
+ 435: 			var added = queue.add(entry);
+ 436: 			if (!added) {
+ 437: 				throw new IllegalStateException("Could not add entry to the queue for task: " + entry.task);
+ 438: 			}
+ 439: 			return entry;
+ 440: 		}
+ 441: 
+ 442: 		@Nullable
+ 443: 		Entry poll() {
+ 444: 			return queue.poll();
+ 445: 		}
+ 446: 
+ 447: 		boolean remove(Entry entry) {
+ 448: 			return queue.remove(entry);
+ 449: 		}
+ 450: 
+ 451: 		boolean isEmpty() {
+ 452: 			return queue.isEmpty();
+ 453: 		}
+ 454: 
+ 455: 		private record Entry(TestTask task, CompletableFuture<@Nullable Void> future, int level, int attempts)
+ 456: 				implements Comparable<Entry> {
+ 457: 			@SuppressWarnings("FutureReturnValueIgnored")
+ 458: 			Entry {
+ 459: 				future.whenComplete((__, t) -> {
+ 460: 					if (t == null) {
+ 461: 						LOGGER.trace(() -> "completed normally: " + this.task());
+ 462: 					}
+ 463: 					else {
+ 464: 						LOGGER.trace(t, () -> "completed exceptionally: " + this.task());
+ 465: 					}
+ 466: 				});
+ 467: 			}
+ 468: 
+ 469: 			Entry incrementAttempts() {
+ 470: 				return new Entry(task(), future, level, attempts + 1);
+ 471: 			}
+ 472: 
+ 473: 			@Override
+ 474: 			public int compareTo(Entry that) {
+ 475: 				var result = Integer.compare(that.level, this.level);
+ 476: 				if (result == 0) {
+ 477: 					return Integer.compare(that.attempts, this.attempts);
+ 478: 				}
+ 479: 				return result;
+ 480: 			}
+ 481: 		}
+ 482: 
+ 483: 	}
+ 484: 
+ 485: 	private class WorkerLeaseManager {
+ 486: 
+ 487: 		private final Semaphore semaphore;
+ 488: 
+ 489: 		WorkerLeaseManager(int parallelism) {
+ 490: 			semaphore = new Semaphore(parallelism);
+ 491: 		}
+ 492: 
+ 493: 		@Nullable
+ 494: 		WorkerLease tryAcquire() {
+ 495: 			boolean acquired = semaphore.tryAcquire();
+ 496: 			if (acquired) {
+ 497: 				LOGGER.trace(() -> "acquired worker lease (available: %d)".formatted(semaphore.availablePermits()));
+ 498: 				return new WorkerLease(this::release);
+ 499: 			}
+ 500: 			return null;
+ 501: 		}
+ 502: 
+ 503: 		private ReacquisitionToken release() {
+ 504: 			semaphore.release();
+ 505: 			LOGGER.trace(() -> "release worker lease (available: %d)".formatted(semaphore.availablePermits()));
+ 506: 			maybeStartWorker();
+ 507: 			return new ReacquisitionToken();
+ 508: 		}
+ 509: 
+ 510: 		boolean isLeaseAvailable() {
+ 511: 			return semaphore.availablePermits() > 0;
+ 512: 		}
+ 513: 
+ 514: 		private class ReacquisitionToken {
+ 515: 
+ 516: 			private boolean used = false;
+ 517: 
+ 518: 			void reacquire() throws InterruptedException {
+ 519: 				Preconditions.condition(!used, "Lease was already reacquired");
+ 520: 				used = true;
+ 521: 				semaphore.acquire();
+ 522: 				LOGGER.trace(() -> "reacquired worker lease (available: %d)".formatted(semaphore.availablePermits()));
+ 523: 			}
+ 524: 		}
+ 525: 	}
+ 526: 
+ 527: 	private static class WorkerLease {
+ 528: 
+ 529: 		private final Supplier<WorkerLeaseManager.ReacquisitionToken> releaseAction;
+ 530: 		private WorkerLeaseManager.@Nullable ReacquisitionToken reacquisitionToken;
+ 531: 
+ 532: 		WorkerLease(Supplier<WorkerLeaseManager.ReacquisitionToken> releaseAction) {
+ 533: 			this.releaseAction = releaseAction;
+ 534: 		}
+ 535: 
+ 536: 		void release() {
+ 537: 			if (reacquisitionToken == null) {
+ 538: 				reacquisitionToken = releaseAction.get();
+ 539: 			}
+ 540: 		}
+ 541: 
+ 542: 		void reacquire() throws InterruptedException {
+ 543: 			Preconditions.notNull(reacquisitionToken, "Cannot reacquire an unreleased WorkerLease");
+ 544: 			reacquisitionToken.reacquire();
+ 545: 			reacquisitionToken = null;
+ 546: 		}
+ 547: 	}
+ 548: 
+ 549: }
```

**The reviewer's comment:**

> Entry.incrementAttempts() builds a new Entry via the canonical constructor, which re-registers a future.whenComplete(...) logging callback (line 459) on the same underlying future each time. When a task is stolen and requeued more than once, this leaves duplicate callbacks on the future, producing duplicate "completed normally/exceptionally" trace log lines when it finally completes.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 18. `anthropic__claude-sonnet-5__junit-team__junit5__5042__unmatched_model__5`

**Arm:** `sonnet`  •  **File:** `platform-tooling-support-tests/src/test/java/platform/tooling/support/tests/JUnitStartTests.java`  •  **comment on line 42**  •  [PR #5042](https://github.com/junit-team/junit5/pull/5042)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2:  * Copyright 2015-2025 the original author or authors.
+ 3:  *
+ 4:  * All rights reserved. This program and the accompanying materials are
+ 5:  * made available under the terms of the Eclipse Public License v2.0 which
+ 6:  * accompanies this distribution and is available at
+ 7:  *
+ 8:  * https://www.eclipse.org/legal/epl-v20.html
+ 9:  */
+ 10: 
+ 11: package platform.tooling.support.tests;
+ 12: 
+ 13: import static org.junit.jupiter.api.Assertions.assertEquals;
+ 14: import static org.junit.jupiter.api.Assertions.assertTrue;
+ 15: import static platform.tooling.support.tests.Projects.copyToWorkspace;
+ 16: 
+ 17: import java.nio.file.Files;
+ 18: import java.nio.file.Path;
+ 19: 
+ 20: import org.junit.jupiter.api.BeforeAll;
+ 21: import org.junit.jupiter.api.Test;
+ 22: import org.junit.jupiter.api.condition.EnabledOnJre;
+ 23: import org.junit.jupiter.api.condition.JRE;
+ 24: import org.junit.jupiter.api.io.TempDir;
+ 25: import org.junit.platform.tests.process.OutputFiles;
+ 26: 
+ 27: import platform.tooling.support.Helper;
+ 28: import platform.tooling.support.MavenRepo;
+ 29: import platform.tooling.support.ProcessStarters;
+ 30: import platform.tooling.support.ThirdPartyJars;
+ 31: 
+ 32: /**
+ 33:  * @since 6.1
+ 34:  */
+ 35: class JUnitStartTests {
+ 36: 
+ 37: 	@TempDir
+ 38: 	static Path workspace;
+ 39: 
+ 40: 	@BeforeAll
+ 41: 	static void prepareLocalLibraryDirectoryWithJUnitModules() throws Exception {
+ 42: 		copyToWorkspace(Projects.JUNIT_start, workspace);
+ 43: 		var lib = workspace.resolve("lib");
+ 44: 		try {
+ 45: 			Files.createDirectories(lib);
+ 46: 			try (var directoryStream = Files.newDirectoryStream(lib, "*.jar")) {
+ 47: 				for (Path jarFile : directoryStream) {
+ 48: 					Files.delete(jarFile);
+ 49: 				}
+ 50: 			}
+ 51: 			for (var module : Helper.loadModuleDirectoryNames()) {
+ 52: 				if (module.startsWith("junit-platform") || module.startsWith("junit-jupiter")
+ 53: 						|| module.equals("junit-start")) {
+ 54: 					if (module.equals("junit-jupiter-migrationsupport"))
+ 55: 						continue;
+ 56: 					if (module.startsWith("junit-platform-suite"))
+ 57: 						continue;
+ 58: 					if (module.equals("junit-platform-testkit"))
+ 59: 						continue;
+ 60: 					var jar = MavenRepo.jar(module);
+ 61: 					Files.copy(jar, lib.resolve(module + ".jar"));
+ 62: 				}
+ 63: 			}
+ 64: 			ThirdPartyJars.copy(lib, "org.apiguardian", "apiguardian-api");
+ 65: 			ThirdPartyJars.copy(lib, "org.jspecify", "jspecify");
+ 66: 			ThirdPartyJars.copy(lib, "org.opentest4j", "opentest4j");
+ 67: 			ThirdPartyJars.copy(lib, "org.opentest4j.reporting", "open-test-reporting-tooling-spi");
+ 68: 		}
+ 69: 		catch (Exception e) {
+ 70: 			throw new AssertionError("Preparing local library folder failed", e);
+ 71: 		}
+ 72: 	}
+ 73: 
+ 74: 	@Test
+ 75: 	@EnabledOnJre(JRE.JAVA_25)
+ 76: 	void junitRun(@FilePrefix("junit-run") OutputFiles outputFiles) throws Exception {
+ 77: 		var result = ProcessStarters.java() //
+ 78: 				.workingDir(workspace) //
+ 79: 				.addArguments("--module-path", "lib") // relative to workspace
+ 80: 				.addArguments("--add-modules", "org.junit.start") // configure root module
+ 81: 				.addArguments("compact/JUnitRun.java") // leverage Java's source mode
+ 82: 				.redirectOutput(outputFiles) //
+ 83: 				.startAndWait();
+ 84: 
+ 85: 		assertEquals(0, result.exitCode());
+ 86: 		assertTrue(result.stdOut().contains("addition()"), result.stdOut());
+ 87: 	}
+ 88: 
+ 89: 	@Test
+ 90: 	@EnabledOnJre(JRE.JAVA_25)
+ 91: 	void junitRunClass(@FilePrefix("junit-run-class") OutputFiles outputFiles) throws Exception {
+ 92: 		var result = ProcessStarters.java() //
+ 93: 				.workingDir(workspace) //
+ 94: 				.addArguments("--module-path", "lib") // relative to workspace
+ 95: 				.addArguments("--add-modules", "org.junit.start") // configure root module
+ 96: 				.addArguments("compact/JUnitRunClass.java") // leverage Java's source mode
+ 97: 				.redirectOutput(outputFiles) //
+ 98: 				.startAndWait();
+ 99: 
+ 100: 		assertEquals(0, result.exitCode());
+ 101: 		assertTrue(result.stdOut().contains("substraction()"), result.stdOut());
+ 102: 	}
+ 103: 
+ 104: 	@Test
+ 105: 	@EnabledOnJre(JRE.JAVA_25)
+ 106: 	void junitRunModule(@FilePrefix("junit-run-Module") OutputFiles outputFiles) throws Exception {
+ 107: 		var result = ProcessStarters.java() //
+ 108: 				.workingDir(workspace) //
+ 109: 				.putEnvironment("NO_COLOR", "1") // --disable-ansi-colors
+ 110: 				.addArguments("--module-path", "lib") // relative to workspace
+ 111: 				.addArguments("modular/p/JUnitRunModule.java") // leverage Java's source mode
+ 112: 				.redirectOutput(outputFiles) //
+ 113: 				.startAndWait();
+ 114: 
+ 115: 		assertEquals(0, result.exitCode());
+ 116: 		assertTrue(result.stdOut().contains("multiplication()"), result.stdOut());
+ 117: 	}
+ 118: 
+ 119: }
```

**The reviewer's comment:**

> Projects.JUNIT_start doesn't follow the ALL_CAPS naming convention normally used for Java constant fields. Is the mixed-case name intentional, or should it be JUNIT_START?

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 19. `anthropic__claude-sonnet-5__mockito__mockito__2603__unmatched_model__0`

**Arm:** `sonnet`  •  **File:** `subprojects/junit-jupiter/src/test/java/org/mockitousage/InjectMocksTest.java`  •  **comment on line 35**  •  [PR #2603](https://github.com/mockito/mockito/pull/2603)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2:  * Copyright (c) 2018 Mockito contributors
+ 3:  * This program is made available under the terms of the MIT License.
+ 4:  */
+ 5: package org.mockitousage;
+ 6: 
+ 7: import org.junit.jupiter.api.Test;
+ 8: import org.junit.jupiter.api.extension.ExtendWith;
+ 9: import org.mockito.InjectMocks;
+ 10: import org.mockito.Mock;
+ 11: import org.mockito.junit.jupiter.MockitoExtension;
+ 12: 
+ 13: import static org.assertj.core.api.Assertions.assertThat;
+ 14: 
+ 15: class ToBeMockedInTestSuperClass{
+ 16:     int identifier;
+ 17: 
+ 18:     public ToBeMockedInTestSuperClass(int identifier) {
+ 19:         this.identifier = identifier;
+ 20:     }
+ 21: }
+ 22: 
+ 23: class ToBeMocked{
+ 24:     int identifier;
+ 25: 
+ 26:     public ToBeMocked(int identifier) {
+ 27:         this.identifier = identifier;
+ 28:     }
+ 29: }
+ 30: 
+ 31: class TestClassToBeInitiatedViaConstructorInSuperClass {
+ 32:     ToBeMockedInTestSuperClass toBeMockedInTestSuperClass;
+ 33: 
+ 34:     public TestClassToBeInitiatedViaConstructorInSuperClass(ToBeMockedInTestSuperClass toBeMockedInTestSuperClass) {
+ 35:         assert toBeMockedInTestSuperClass != null;
+ 36:         this.toBeMockedInTestSuperClass = new ToBeMockedInTestSuperClass(42);
+ 37:     }
+ 38: }
+ 39: 
+ 40: class TestClassToBeInitiatedViaConstructor{
+ 41:     ToBeMockedInTestSuperClass toBeMockedInTestSuperClass;
+ 42:     ToBeMocked toBeMocked;
+ 43: 
+ 44:     public TestClassToBeInitiatedViaConstructor(ToBeMocked toBeMocked, ToBeMockedInTestSuperClass toBeMockedInTestSuperClass) {
+ 45:         assert toBeMocked != null;
+ 46:         assert toBeMockedInTestSuperClass != null;
+ 47:         this.toBeMocked = new ToBeMocked(42);
+ 48:         this.toBeMockedInTestSuperClass = new ToBeMockedInTestSuperClass(42);
+ 49:     }
+ 50: }
+ 51: 
+ 52: class SuperTestClass {
+ 53:     @Mock
+ 54:     ToBeMockedInTestSuperClass toBeMockedInTestSuperClass;
+ 55: 
+ 56:     @InjectMocks
+ 57:     TestClassToBeInitiatedViaConstructorInSuperClass testClassToBeInitiatedViaConstructorInSuperClass;
+ 58: 
+ 59: }
+ 60: 
+ 61: @ExtendWith(MockitoExtension.class)
+ 62: class InjectMocksTest extends SuperTestClass {
+ 63: 
+ 64:     @Mock
+ 65:     ToBeMocked toBeMocked;
+ 66: 
+ 67:     @InjectMocks
+ 68:     TestClassToBeInitiatedViaConstructor testClassToBeInitiatedViaConstructor;
+ 69: 
+ 70:     /**
+ 71:      * Checks that {@link #testClassToBeInitiatedViaConstructor} holds instances that have identifier 42.
+ 72:      * It being 42 is proof that constructor injection was used over field injection.
+ 73:      */
+ 74:     @Test
+ 75:     void given_instanceToBeInitializedByMockito_when_mocksRequestedByConstructorAreInTestAndSuperClass_should_useConstructorInjection() {
+ 76:         assertThat(testClassToBeInitiatedViaConstructor)
+ 77:             .extracting(
+ 78:                 testInstance-> testInstance.toBeMocked.identifier,
+ 79:                 testInstance-> testInstance.toBeMockedInTestSuperClass.identifier
+ 80:             )
+ 81:             .containsExactly(
+ 82:                 42,
+ 83:                 42
+ 84:             );
+ 85:     }
+ 86: 
+ 87:     /**
+ 88:      * Checks that {@link #testClassToBeInitiatedViaConstructorInSuperClass} holds instances that have identifier 42.
+ 89:      * It being 42 is proof that constructor injection was used over field injection.
+ 90:      */
+ 91:     @Test
+ 92:     public void given_instanceInSuperClassToBeInitializedByMockito_when_mocksRequestedAreInSuperClass_should_useConstructorInjection(){
+ 93:         assertThat(testClassToBeInitiatedViaConstructorInSuperClass)
+ 94:             .extracting(yetAnotherClas1 -> yetAnotherClas1.toBeMockedInTestSuperClass.identifier)
+ 95:             .isEqualTo(42);
+ 96:     }
+ 97: 
+ 98: }
```

**The reviewer's comment:**

> Null-checking constructor arguments with Java's `assert` keyword relies on JVM assertions being enabled (-ea); since they're disabled by default, this check (and the ones at lines 45-46) silently does nothing in a typical run and doesn't actually guard against null mocks.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 20. `claude-code-subagent__opus__mockito__mockito__2807__unmatched_model__9`

**Arm:** `opus`  •  **File:** `src/main/java/org/mockito/internal/matchers/InstanceOf.java`  •  **comment on line 54**  •  [PR #2807](https://github.com/mockito/mockito/pull/2807)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  1: /*
  2:  * Copyright (c) 2007 Mockito contributors
  3:  * This program is made available under the terms of the MIT License.
  4:  */
  5: package org.mockito.internal.matchers;
  6: 
  7: import java.io.Serializable;
  8: 
  9: import org.mockito.ArgumentMatcher;
  10: import org.mockito.internal.util.Primitives;
  11: 
  12: public class InstanceOf implements ArgumentMatcher<Object>, Serializable {
  13: 
- :     private final Class<?> clazz;
+ 14:     final Class<?> clazz;
  15:     private final String description;
  16: 
  17:     public InstanceOf(Class<?> clazz) {
  18:         this(clazz, "isA(" + clazz.getCanonicalName() + ")");
  19:     }
  20: 
  21:     public InstanceOf(Class<?> clazz, String describedAs) {
  22:         this.clazz = clazz;
  23:         this.description = describedAs;
  24:     }
  25: 
  26:     @Override
  27:     public boolean matches(Object actual) {
  28:         return (actual != null)
  29:                 && (Primitives.isAssignableFromWrapper(actual.getClass(), clazz)
  30:                         || clazz.isAssignableFrom(actual.getClass()));
  31:     }
  32: 
+ 33:     @Override
+ 34:     public Class<?> type() {
+ 35:         return clazz;
+ 36:     }
+ 37: 
  38:     @Override
  39:     public String toString() {
  40:         return description;
  41:     }
  42: 
  43:     public static class VarArgAware extends InstanceOf implements VarargMatcher {
  44: 
  45:         public VarArgAware(Class<?> clazz) {
  46:             super(clazz);
  47:         }
  48: 
  49:         public VarArgAware(Class<?> clazz, String describedAs) {
  50:             super(clazz, describedAs);
  51:         }
+ 52: 
+ 53:         @Override
+ 54:         public Class<?> type() {
+ 55:             return clazz;
+ 56:         }
  57:     }
  58: }
```

**The reviewer's comment:**

> This override returns exactly what the inherited `InstanceOf.type()` returns, so it adds nothing. Dropping it keeps the subclass to the behaviour it actually changes (implementing `VarargMatcher`).

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 21. `qwen__qwen3-coder-30b-a3b-instruct__checkstyle__checkstyle__20600__unmatched_model__49`

**Arm:** `qwen`  •  **File:** `src/test/resources/com/puppycrawl/tools/checkstyle/checks/multilinecommentleadingasteriskpresence/InputMultilineCommentLeadingAsteriskPresenceJavadoc.java`  •  **comment on line 1**  •  [PR #20600](https://github.com/checkstyle/checkstyle/pull/20600)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2: MultilineCommentLeadingAsteriskPresence
+ 3: 
+ 4: */
+ 5: // violation 3 lines above 'Multiline comment should start with leading asterisk'
+ 6: // violation 3 lines above 'Multiline comment should start with leading asterisk'
+ 7: 
+ 8: package com.puppycrawl.tools.checkstyle.checks.multilinecommentleadingasteriskpresence;
+ 9: 
+ 10: public class InputMultilineCommentLeadingAsteriskPresenceJavadoc {
+ 11: 
+ 12:     /**
+ 13:        This method has javadoc
+ 14: 
+ 15:      * @param a array of integers
+ 16:      */
+ 17:     void method(int... a) {
+ 18:         return;
+ 19:     }
+ 20: 
+ 21:     /**
+ 22:        Line 1
+ 23:        Line 2
+ 24:        Line 3
+ 25:      */
+ 26:     void foo() {}
+ 27: 
+ 28:     /* This method is empty. */
+ 29:     void foo1() {}
+ 30: 
+ 31:     /** Line 1
+ 32: 
+ 33:         Line 3
+ 34: 
+ 35:         Line 4
+ 36:       */
+ 37:     void bar() {}
+ 38: }
```

**The reviewer's comment:**

> The multiline comment on lines 1-4 should start with a leading asterisk on each line for consistency with the check's requirements.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 22. `qwen__qwen3-coder-30b-a3b-instruct__checkstyle__checkstyle__20537__unmatched_model__17`

**Arm:** `qwen`  •  **File:** `src/test/resources/com/puppycrawl/tools/checkstyle/checks/coding/unusedlocalvariable/InputUnusedLocalVariableAllowNamedPatternVariables.java`  •  **comment on line 36**  •  [PR #20537](https://github.com/checkstyle/checkstyle/pull/20537)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  1: /*
  2: UnusedLocalVariable
  3: allowUnnamedVariables = false
  4: jdkVersion = 23
  5: 
  6: */
  7: package com.puppycrawl.tools.checkstyle.checks.coding.unusedlocalvariable;
  8: 
  9: public class InputUnusedLocalVariableAllowNamedPatternVariables {
  10:     record Ignored(int x, int y) {}
+ 11:     sealed interface Customer {}
+ 12:     record Person(String name, int age) implements Customer {}
+ 13:     record Company(String name) implements Customer {}
+ 14:     sealed interface Maybe<T> {}
+ 15:     record None<T>() implements Maybe<T> {}
+ 16:     record Some<T>(T value) implements Maybe<T> {}
+ 17: 
  18: 
  19:     String whatClass(Object object) {
  20:         return switch (object) {
  21:             case String ignored -> "A String"; // violation, 'Unused local variable'
  22:             case Integer ignored2 -> "An Integer"; // violation, 'Unused local variable'
  23:             default -> "Something Else";
  24:         };
  25:     }
  26: 
  27:     void method(Object object) {
  28:         int x = 10; // violation, 'Unused local variable'
  29:         if (object instanceof String ignored) { // violation, 'Unused local variable'
  30:             System.out.println("string");
  31:         }
  32:     }
  33: 
  34:     String withrecord(Object object) {
  35:         return switch (object) { // violation below, unused local variable 'y'
  36:             case Ignored(int y, int z) -> "record switch"; // violation, unused local variable 'z'
  37:             default -> "other";
  38:         };
  39:     }
+ 40: 
+ 41:     String name(Customer customer) { // violation below, 'Unused local variable'
+ 42:         if (customer instanceof Person(String name, int ignoredAge)) {
+ 43:             return name;
+ 44:         } else if (customer instanceof Company(String companyName)) {
+ 45:             return companyName;
+ 46:         }
+ 47:         throw new IllegalStateException();
+ 48:     }
+ 49: 
+ 50:     boolean isNested(Maybe<?> maybe) {
+ 51:         if (maybe instanceof Some(Some<?> inner)) { // violation, 'Unused local variable'
+ 52:             return true;
+ 53:         }
+ 54:         return false;
+ 55:     }
+ 56: 
  57: }
```

**The reviewer's comment:**

> The variable 'z' is unused in the pattern match. Consider if this is intentional or if the variable should be named differently to indicate its purpose.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 23. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5379__unmatched_model__113`

**Arm:** `qwen`  •  **File:** `jupiter-tests/src/test/java/org/junit/jupiter/engine/extension/TimeoutConfigurationTests.java`  •  **comment on line 33**  •  [PR #5379](https://github.com/junit-team/junit5/pull/5379)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  9:  */
  10: 
  11: package org.junit.jupiter.engine.extension;
  12: 
  13: import static java.util.concurrent.TimeUnit.DAYS;
  14: import static java.util.concurrent.TimeUnit.HOURS;
  15: import static java.util.concurrent.TimeUnit.MICROSECONDS;
  16: import static java.util.concurrent.TimeUnit.MILLISECONDS;
  17: import static java.util.concurrent.TimeUnit.MINUTES;
  18: import static java.util.concurrent.TimeUnit.NANOSECONDS;
  19: import static java.util.concurrent.TimeUnit.SECONDS;
  20: import static org.assertj.core.api.Assertions.assertThat;
  21: import static org.assertj.core.api.Assertions.assertThatThrownBy;
+ 22: import static org.junit.jupiter.api.Constants.DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
+ 23: import static org.junit.jupiter.api.Constants.DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
+ 24: import static org.junit.jupiter.api.Constants.DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
+ 25: import static org.junit.jupiter.api.Constants.DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
+ 26: import static org.junit.jupiter.api.Constants.DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 27: import static org.junit.jupiter.api.Constants.DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 28: import static org.junit.jupiter.api.Constants.DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME;
+ 29: import static org.junit.jupiter.api.Constants.DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME;
+ 30: import static org.junit.jupiter.api.Constants.DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 31: import static org.junit.jupiter.api.Constants.DEFAULT_TIMEOUT_PROPERTY_NAME;
+ 32: import static org.junit.jupiter.api.Constants.DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME;
  33: import static org.junit.jupiter.api.Timeout.TIMEOUT_MODE_PROPERTY_NAME;
  34: import static org.junit.jupiter.api.Timeout.ThreadMode.SEPARATE_THREAD;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_TIMEOUT_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME;
  35: import static org.mockito.ArgumentMatchers.any;
  36: import static org.mockito.ArgumentMatchers.eq;
  37: import static org.mockito.Mockito.mock;
  38: import static org.mockito.Mockito.when;
  39: 
  40: import java.util.Optional;
  41: import java.util.function.Function;
  42: import java.util.logging.Level;
  43: import java.util.logging.LogRecord;
  44: 
  45: import org.junit.jupiter.api.Test;
  46: import org.junit.jupiter.api.extension.ExtensionContext;
  47: import org.junit.jupiter.api.fixtures.TrackLogRecords;
```

**The reviewer's comment:**

> Consider grouping related imports together for better readability

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 24. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5042__unmatched_model__31`

**Arm:** `qwen`  •  **File:** `platform-tooling-support-tests/projects/jar-describe-module/junit-platform-console.expected.txt`  •  **comment on line 13**  •  [PR #5042](https://github.com/junit-team/junit5/pull/5042)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  1: org.junit.platform.console@${version} jar:file:.+/junit-platform-console-\d.+\.jar..module-info\.class
  2: requires java.base mandated
  3: requires org.apiguardian.api static
  4: requires org.jspecify static transitive
  5: requires org.junit.platform.commons
  6: requires org.junit.platform.engine
  7: requires org.junit.platform.launcher
  8: requires org.junit.platform.reporting
  9: provides java.util.spi.ToolProvider with org.junit.platform.console.ConsoleLauncherToolProvider
+ 10: qualified exports org.junit.platform.console.output to org.junit.start
  11: contains org.junit.platform.console
  12: contains org.junit.platform.console.command
  13: contains org.junit.platform.console.options
- : contains org.junit.platform.console.output
  14: contains org.junit.platform.console.shadow.picocli
  15: main-class org.junit.platform.console.ConsoleLauncher
```

**The reviewer's comment:**

> Duplicate 'contains org.junit.platform.console.output' line. The previous occurrence was removed but this line was added, creating a duplicate entry.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 25. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5135__unmatched_model__21`

**Arm:** `qwen`  •  **File:** `platform-tests/src/test/java/org/junit/platform/engine/support/hierarchical/WorkerThreadPoolHierarchicalTestExecutorServiceTests.java`  •  **comment on line 524**  •  [PR #5135](https://github.com/junit-team/junit5/pull/5135)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  473: 					.withName("root").withLevel(1);
  474: 
  475: 		service.submit(root).get();
  476: 
  477: 		assertThat(List.of(root, leaf1a, leaf1b, leaf1c, leaf1d)) //
  478: 				.allSatisfy(TestTaskStub::assertExecutedSuccessfully);
  479: 
  480: 		assertThat(children) //
  481: 				.extracting(TestTaskStub::startTime) //
  482: 				.isSorted();
  483: 	}
  484: 
  485: 	@Test
- : 	void workIsStolenInReverseOrder() throws Exception {
+ 486: 	void testsAreStolenRatherThanContainers() throws Exception {
  487: 		service = new WorkerThreadPoolHierarchicalTestExecutorService(configuration(2, 2));
  488: 
  489: 		// Execute tasks pairwise
  490: 		CyclicBarrier cyclicBarrier = new CyclicBarrier(2);
  491: 		Executable behavior = cyclicBarrier::await;
  492: 
- : 		// With half of the leaves to be executed normally
- : 		var leaf1a = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
- : 				.withName("leaf1a").withLevel(2);
- : 		var leaf1b = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
- : 				.withName("leaf1b").withLevel(2);
- : 		var leaf1c = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
- : 				.withName("leaf1c").withLevel(2);
- : 
- : 		// And half of the leaves to be stolen
- : 		var leaf2a = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
- : 				.withName("leaf2a").withLevel(2);
- : 		var leaf2b = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
- : 				.withName("leaf2b").withLevel(2);
- : 		var leaf2c = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
- : 				.withName("leaf2c").withLevel(2);
+ 493: 		// With half of the leaves being containers
+ 494: 		var container1 = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
+ 495: 				.withName("container1").withType(CONTAINER).withLevel(2);
+ 496: 		var container2 = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
+ 497: 				.withName("container2").withType(CONTAINER).withLevel(2);
+ 498: 		var container3 = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
+ 499: 				.withName("container3").withType(CONTAINER).withLevel(2);
+ 500: 
+ 501: 		// And half of the leaves being tests, to be stolen
+ 502: 		var test1 = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
+ 503: 				.withName("test1").withType(TEST).withLevel(2);
+ 504: 		var test2 = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
+ 505: 				.withName("test2").withType(TEST).withLevel(2);
+ 506: 		var test3 = new TestTaskStub(ExecutionMode.CONCURRENT, behavior) //
+ 507: 				.withName("test3").withType(TEST).withLevel(2);
  508: 
  509: 		var root = new TestTaskStub(ExecutionMode.SAME_THREAD,
- : 			() -> requiredService().invokeAll(List.of(leaf1a, leaf1b, leaf1c, leaf2a, leaf2b, leaf2c))) //
+ 510: 			() -> requiredService().invokeAll(List.of(container1, container2, container3, test1, test2, test3))) //
  511: 					.withName("root").withLevel(1);
  512: 
  513: 		service.submit(root).get();
  514: 
- : 		assertThat(List.of(root, leaf1a, leaf1b, leaf1c, leaf2a, leaf2b, leaf2c)) //
+ 515: 		assertThat(List.of(root, container1, container2, container3, test1, test2, test3)) //
  516: 				.allSatisfy(TestTaskStub::assertExecutedSuccessfully);
  517: 
- : 		// If the last node was stolen.
- : 		assertThat(leaf1a.executionThread).isNotEqualTo(leaf2c.executionThread);
- : 		// Then it must follow that the last half of the nodes were stolen
- : 		assertThat(Stream.of(leaf1a, leaf1b, leaf1c)) //
+ 518: 		// If the last test node was stolen
+ 519: 		assertThat(container1.executionThread).isNotEqualTo(test3.executionThread);
+ 520: 		// Then it must follow that the test nodes were stolen
+ 521: 		assertThat(Stream.of(container1, container2, container3)) //
  522: 				.extracting(TestTaskStub::executionThread) //
- : 				.containsOnly(leaf1a.executionThread);
- : 		assertThat(Stream.of(leaf2a, leaf2b, leaf2c)) //
+ 523: 				.containsOnly(container1.executionThread);
+ 524: 		assertThat(Stream.of(test1, test2, test3)) //
  525: 				.extracting(TestTaskStub::executionThread) //
- : 				.containsOnly(leaf2c.executionThread);
+ 526: 				.containsOnly(test3.executionThread);
  527: 
- : 		assertThat(Stream.of(leaf1a, leaf1b, leaf1c)) //
+ 528: 		assertThat(Stream.of(container1, container2, container3)) //
  529: 				.extracting(TestTaskStub::startTime) //
  530: 				.isSorted();
- : 		assertThat(Stream.of(leaf2c, leaf2b, leaf2a)) //
+ 531: 		assertThat(Stream.of(test1, test2, test3)) //
  532: 				.extracting(TestTaskStub::startTime) //
  533: 				.isSorted();
  534: 	}
  535: 
  536: 	@Test
  537: 	void stealsDynamicChildren() throws Exception {
  538: 		service = new WorkerThreadPoolHierarchicalTestExecutorService(configuration(2, 2));
  539: 
  540: 		var child1Started = new CountDownLatch(1);
  541: 		var child2Finished = new CountDownLatch(1);
  542: 		var child1 = new TestTaskStub(ExecutionMode.CONCURRENT, () -> {
  543: 			child1Started.countDown();
  544: 			child2Finished.await();
```

**The reviewer's comment:**

> The assertion 'Stream.of(test1, test2, test3).extracting(TestTaskStub::executionThread).containsOnly(test3.executionThread)' only checks that all tests ran on the same thread as test3, but doesn't verify that tests were stolen from other threads.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 26. `qwen__qwen3-coder-30b-a3b-instruct__checkstyle__checkstyle__21086__unmatched_model__38`

**Arm:** `qwen`  •  **File:** `src/site/xdoc/checks/javadoc/writetag.xml`  •  **comment on line 427**  •  [PR #21086](https://github.com/checkstyle/checkstyle/pull/21086)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  404: 
  405:       <subsection name="Example of Usage" id="WriteTag_Example_of_Usage">
  406:         <ul>
  407:           <li>
  408:             <a href="https://github.com/search?q=path%3Aconfig%20path%3A**%2Fcheckstyle-checks.xml+repo%3Acheckstyle%2Fcheckstyle+WriteTag">
  409:             Checkstyle Style</a>
  410:           </li>
  411:         </ul>
  412:       </subsection>
  413: 
  414:       <subsection name="Violation Messages" id="WriteTag_Violation_Messages">
  415:         <ul>
  416:           <li>
- :             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22javadoc.parse.rule.error%22">
- :               javadoc.parse.rule.error
+ 417:             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22javadoc.missingTag%22">
+ 418:               javadoc.missingTag
  419:             </a>
  420:           </li>
  421:           <li>
- :             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22javadoc.unclosedHtml%22">
- :               javadoc.unclosedHtml
+ 422:             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22javadoc.parse.rule.error%22">
+ 423:               javadoc.parse.rule.error
  424:             </a>
  425:           </li>
  426:           <li>
- :             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22javadoc.writeTag%22">
- :               javadoc.writeTag
+ 427:             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22javadoc.tagFormat%22">
+ 428:               javadoc.tagFormat
  429:             </a>
  430:           </li>
  431:           <li>
- :             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22type.missingTag%22">
- :               type.missingTag
+ 432:             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22javadoc.unclosedHtml%22">
+ 433:               javadoc.unclosedHtml
  434:             </a>
  435:           </li>
  436:           <li>
- :             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22type.tagFormat%22">
- :               type.tagFormat
+ 437:             <a href="https://github.com/search?q=path%3Asrc%2Fmain%2Fresources%2Fcom%2Fpuppycrawl%2Ftools%2Fcheckstyle%2Fchecks%2Fjavadoc+path%3A**%2Fmessages*.properties+repo%3Acheckstyle%2Fcheckstyle+%22javadoc.writeTag%22">
+ 438:               javadoc.writeTag
  439:             </a>
  440:           </li>
  441:         </ul>
  442:         <p>
  443:           All messages can be customized if the default message doesn't suit you.
  444:           Please <a href="../../config.html#Custom_messages">see the documentation</a>
  445:           to learn how to.
  446:         </p>
  447:       </subsection>
  448: 
  449:       <subsection name="Fully Qualified Name" id="WriteTag_Fully_Qualified_Name">
  450:         <p>com.puppycrawl.tools.checkstyle.checks.javadoc.WriteTagCheck</p>
  451:         <p>
```

**The reviewer's comment:**

> The link for 'javadoc.tagFormat' appears to be incorrect, pointing to 'javadoc.writeTag' instead.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 27. `qwen__qwen3-coder-30b-a3b-instruct__checkstyle__checkstyle__20600__unmatched_model__15`

**Arm:** `qwen`  •  **File:** `src/main/resources/com/puppycrawl/tools/checkstyle/checks/messages_es.properties`  •  **comment on line 9**  •  [PR #20600](https://github.com/checkstyle/checkstyle/pull/20600)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  1: array.type.style=Soportes de matriz en posición ilegal.
  2: descendant.token.max=El recuento {0} para ''{2}'' descendientes ''{3}'' excede el máximo {1}.
  3: descendant.token.min=El recuento {0} para ''{2}'' descendientes ''{3}'' es menor que el mínimo {1}.
  4: descendant.token.sum.max=Recuento total de {0} excede el máximo recuento {1} en ''{2}''.
  5: descendant.token.sum.min=Recuento total de {0} es menor que el recuento mínimo {1} en ''{2}''.
  6: final.parameter=El parámetro {0} debería ser final.
  7: forbid.escaped.unicode.char=El uso de Unicode de escape (s) debe ser evitado.
  8: hex.literal=Se deben usar letras hexadecimales en mayúsculas.
+ 9: multiline.comment.missing.asterisk=Los comentarios de varias líneas deben comenzar con un asterisco inicial.
  10: nocode.in.file=El archivo no contiene ningún código.
  11: noNewlineAtEOF=El fichero no termina con un retorno de carro.
  12: numerical.literal.infix=Se deben usar infijos numéricos en minúsculas.
  13: numerical.literal.prefix=Se deben usar prefijos numéricos en minúsculas.
  14: numerical.literal.suffix=Se deben usar sufijos numéricos en minúsculas.
  15: properties.duplicate.property=Propiedad duplicado ''{0}'' {1} ocurrencia (s)).
  16: properties.notSorted.property=Clave de propiedad ''{0}'' no está en el orden correcto con la propiedad anterior ''{1}''.
  17: todo.match=El comentario coincide con el formato to-do ''{0}''.
  18: trailing.comments=No usar comentarios de final de línea.
  19: translation.missingKey=La clave ''{0}'' falta.
  20: translation.missingTranslationFile=Archivo de propiedades ''{0}'' no se encuentra.
  21: translation.wrongLanguageCode=Código de idioma especificado ''{0}'' no es correcta.
  22: type.file.mismatch=El nombre del tipo externo y el archivo no coinciden.
```

**The reviewer's comment:**

> The Spanish translation for 'multiline.comment.missing.asterisk' uses 'comenzar' which is less precise than 'debe comenzar' used in English. Consider using 'debe comenzar' for consistency.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 28. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5379__unmatched_model__129`

**Arm:** `qwen`  •  **File:** `platform-tests/src/test/java/org/junit/platform/suite/engine/testsuites/ConfigurationSuite.java`  •  **comment on line 13**  •  [PR #5379](https://github.com/junit-team/junit5/pull/5379)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

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
  11: package org.junit.platform.suite.engine.testsuites;
  12: 
- : import static org.junit.jupiter.engine.Constants.DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME;
+ 13: import static org.junit.jupiter.api.Constants.DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME;
  14: 
  15: import org.junit.platform.suite.api.ConfigurationParameter;
  16: import org.junit.platform.suite.api.SelectClasses;
  17: import org.junit.platform.suite.api.Suite;
  18: import org.junit.platform.suite.engine.testcases.ConfigurationSensitiveTestCase;
  19: 
  20: @Suite
  21: @ConfigurationParameter(key = DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME, value = "per_class")
  22: @SelectClasses(ConfigurationSensitiveTestCase.class)
  23: public class ConfigurationSuite {
  24: }
```

**The reviewer's comment:**

> Incorrect import: DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME was moved from org.junit.jupiter.engine.Constants to org.junit.jupiter.api.Constants. The old import path is no longer valid and will cause compilation failure.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 29. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5379__unmatched_model__104`

**Arm:** `qwen`  •  **File:** `jupiter-tests/src/test/java/org/junit/jupiter/engine/extension/OrderedMethodTests.java`  •  **comment on line 17**  •  [PR #5379](https://github.com/junit-team/junit5/pull/5379)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  2:  * Copyright 2015-2026 the original author or authors.
  3:  *
  4:  * All rights reserved. This program and the accompanying materials are
  5:  * made available under the terms of the Eclipse Public License v2.0 which
  6:  * accompanies this distribution and is available at
  7:  *
  8:  * https://www.eclipse.org/legal/epl-v20.html
  9:  */
  10: 
  11: package org.junit.jupiter.engine.extension;
  12: 
  13: import static java.util.Comparator.comparing;
  14: import static org.assertj.core.api.Assertions.assertThat;
+ 15: import static org.junit.jupiter.api.Constants.DEFAULT_EXECUTION_MODE_PROPERTY_NAME;
+ 16: import static org.junit.jupiter.api.Constants.DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME;
+ 17: import static org.junit.jupiter.api.Constants.PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME;
+ 18: import static org.junit.jupiter.api.Constants.PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME;
  19: import static org.junit.jupiter.api.DynamicTest.dynamicTest;
  20: import static org.junit.jupiter.api.MethodOrderer.Random.RANDOM_SEED_PROPERTY_NAME;
  21: import static org.junit.jupiter.api.Order.DEFAULT;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_PARALLEL_EXECUTION_MODE;
- : import static org.junit.jupiter.engine.Constants.DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME;
- : import static org.junit.jupiter.engine.Constants.PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME;
  22: import static org.junit.platform.engine.discovery.DiscoverySelectors.selectClass;
  23: import static org.junit.platform.launcher.LauncherConstants.CRITICAL_DISCOVERY_ISSUE_SEVERITY_PROPERTY_NAME;
  24: 
  25: import java.lang.annotation.Annotation;
  26: import java.lang.reflect.Method;
  27: import java.util.Collections;
  28: import java.util.HashSet;
  29: import java.util.LinkedHashSet;
  30: import java.util.List;
  31: import java.util.Map;
  32: import java.util.Optional;
  33: import java.util.Set;
  34: import java.util.logging.Level;
```

**The reviewer's comment:**

> Consider grouping imports from the same package together for better readability

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 30. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5379__unmatched_model__75`

**Arm:** `qwen`  •  **File:** `junit-jupiter-engine/src/main/java/org/junit/jupiter/engine/extension/MutableExtensionRegistry.java`  •  **comment on line 34**  •  [PR #5379](https://github.com/junit-team/junit5/pull/5379)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  21: import java.util.LinkedHashMap;
  22: import java.util.LinkedHashSet;
  23: import java.util.List;
  24: import java.util.Map;
  25: import java.util.Optional;
  26: import java.util.ServiceLoader;
  27: import java.util.Set;
  28: import java.util.function.Function;
  29: import java.util.function.Predicate;
  30: import java.util.stream.Stream;
  31: 
  32: import org.apiguardian.api.API;
  33: import org.jspecify.annotations.Nullable;
+ 34: import org.junit.jupiter.api.Constants;
  35: import org.junit.jupiter.api.extension.Extension;
  36: import org.junit.jupiter.engine.config.JupiterConfiguration;
  37: import org.junit.platform.commons.logging.Logger;
  38: import org.junit.platform.commons.logging.LoggerFactory;
  39: import org.junit.platform.commons.support.ReflectionSupport;
  40: import org.junit.platform.commons.util.ClassLoaderUtils;
  41: import org.junit.platform.commons.util.Preconditions;
  42: import org.junit.platform.commons.util.ServiceLoaderUtils;
  43: 
  44: /**
  45:  * Default, mutable implementation of {@link ExtensionRegistry}.
  46:  *
  47:  * @since 5.5
```

**The reviewer's comment:**

> Consider grouping imports from the same package together for better readability

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 31. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5060__unmatched_model__23`

**Arm:** `qwen`  •  **File:** `junit-platform-engine/src/main/java/org/junit/platform/engine/support/hierarchical/CompositeLock.java`  •  **comment on line 51**  •  [PR #5060](https://github.com/junit-team/junit5/pull/5060)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  35: 			resource -> resource.getLockMode() == ExclusiveResource.LockMode.READ_WRITE);
  36: 	}
  37: 
  38: 	@Override
  39: 	public List<ExclusiveResource> getResources() {
  40: 		return resources;
  41: 	}
  42: 
  43: 	// for tests only
  44: 	List<Lock> getLocks() {
  45: 		return this.locks;
  46: 	}
  47: 
+ 48: 	@Override
+ 49: 	public boolean tryAcquire() {
+ 50: 		List<Lock> acquiredLocks = new ArrayList<>(this.locks.size());
+ 51: 		for (Lock lock : this.locks) {
+ 52: 			if (lock.tryLock()) {
+ 53: 				acquiredLocks.add(lock);
+ 54: 			}
+ 55: 			else {
+ 56: 				break;
+ 57: 			}
+ 58: 		}
+ 59: 		if (acquiredLocks.size() == this.locks.size()) {
+ 60: 			return true;
+ 61: 		}
+ 62: 		else {
+ 63: 			release(acquiredLocks);
+ 64: 			return false;
+ 65: 		}
+ 66: 	}
+ 67: 
  68: 	@Override
  69: 	public ResourceLock acquire() throws InterruptedException {
  70: 		ForkJoinPool.managedBlock(new CompositeLockManagedBlocker());
  71: 		return this;
  72: 	}
  73: 
  74: 	private void acquireAllLocks() throws InterruptedException {
  75: 		List<Lock> acquiredLocks = new ArrayList<>(this.locks.size());
  76: 		try {
  77: 			for (Lock lock : this.locks) {
  78: 				lock.lockInterruptibly();
  79: 				acquiredLocks.add(lock);
  80: 			}
```

**The reviewer's comment:**

> Potential deadlock risk in tryAcquire() method. If a lock acquisition fails partway through the loop, the previously acquired locks are released, but there's no mechanism to prevent other threads from acquiring the same locks between the failure and release, potentially leading to inconsistent state.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 32. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5424__unmatched_model__8`

**Arm:** `qwen`  •  **File:** `junit-jupiter-api/src/testFixtures/java/org/junit/jupiter/api/io/FailingTempDirDeletionStrategy.java`  •  **comment on line 30**  •  [PR #5424](https://github.com/junit-team/junit5/pull/5424)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
+ 1: /*
+ 2:  * Copyright 2026 the original author or authors.
+ 3:  *
+ 4:  * All rights reserved. This program and the accompanying materials are
+ 5:  * made available under the terms of the Eclipse Public License v2.0 which
+ 6:  * accompanies this distribution and is available at
+ 7:  *
+ 8:  * https://www.eclipse.org/legal/epl-v20.html
+ 9:  */
+ 10: 
+ 11: package org.junit.jupiter.api.io;
+ 12: 
+ 13: import java.io.IOException;
+ 14: import java.nio.file.Files;
+ 15: import java.nio.file.Path;
+ 16: 
+ 17: import org.jspecify.annotations.NullMarked;
+ 18: import org.junit.jupiter.api.extension.AnnotatedElementContext;
+ 19: import org.junit.jupiter.api.extension.ExtensionContext;
+ 20: 
+ 21: @NullMarked
+ 22: public class FailingTempDirDeletionStrategy implements TempDirDeletionStrategy {
+ 23: 
+ 24: 	public static final Path UNDELETABLE_PATH = Path.of("undeletable");
+ 25: 
+ 26: 	@Override
+ 27: 	public DeletionResult delete(Path tempDir, AnnotatedElementContext elementContext,
+ 28: 			ExtensionContext extensionContext) throws IOException {
+ 29: 
+ 30: 		return Standard.INSTANCE.delete(tempDir, path -> {
+ 31: 			if (path.endsWith(UNDELETABLE_PATH)) {
+ 32: 				throw new IOException("Simulated failure");
+ 33: 			}
+ 34: 			else {
+ 35: 				Files.delete(path);
+ 36: 			}
+ 37: 		});
+ 38: 	}
+ 39: }
```

**The reviewer's comment:**

> The lambda in the delete method may not properly handle all paths, as it only checks if the path ends with UNDELETABLE_PATH. This could lead to incorrect behavior if the path contains this string in a different context.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 33. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5424__unmatched_model__23`

**Arm:** `qwen`  •  **File:** `junit-jupiter-engine/src/main/java/org/junit/jupiter/engine/extension/TempDirectory.java`  •  **comment on line 217**  •  [PR #5424](https://github.com/junit-team/junit5/pull/5424)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  130: 		if (!isRecordObject(instance)) {
  131: 			injectFields(context, instance, instance.getClass(), ModifierSupport::isNotStatic);
  132: 		}
  133: 	}
  134: 
  135: 	private void injectFields(ExtensionContext context, @Nullable Object testInstance, Class<?> testClass,
  136: 			Predicate<Field> predicate) {
  137: 
  138: 		findAnnotatedFields(testClass, TempDir.class, predicate).forEach(field -> {
  139: 			assertNonFinalField(field);
  140: 			assertSupportedType("field", field.getType());
  141: 
  142: 			try {
- : 				CleanupMode cleanupMode = determineCleanupModeForField(field);
- : 				TempDirFactory factory = determineTempDirFactoryForField(field);
+ 143: 				TempDir tempDir = findAnnotationOnField(field);
  144: 				makeAccessible(field).set(testInstance,
- : 					getPathOrFile(field.getType(), new FieldContext(field), factory, cleanupMode, context));
+ 145: 					getPathOrFile(field.getType(), new FieldContext(field), context, tempDir));
  146: 			}
  147: 			catch (Throwable t) {
  148: 				throw ExceptionUtils.throwAsUncheckedException(t);
  149: 			}
  150: 		});
  151: 	}
  152: 
  153: 	/**
  154: 	 * Determine if the {@link Parameter} in the supplied {@link ParameterContext}
  155: 	 * is annotated with {@link TempDir @TempDir}.
  156: 	 */
  157: 	@Override
  158: 	public boolean supportsParameter(ParameterContext parameterContext, ExtensionContext extensionContext) {
  159: 		return parameterContext.isAnnotated(TempDir.class);
  160: 	}
  161: 
  162: 	/**
  163: 	 * Resolve the current temporary directory for the {@link Parameter} in the
  164: 	 * supplied {@link ParameterContext}.
  165: 	 */
  166: 	@Override
  167: 	public Object resolveParameter(ParameterContext parameterContext, ExtensionContext extensionContext) {
  168: 		Class<?> parameterType = parameterContext.getParameter().getType();
  169: 		assertSupportedType("parameter", parameterType);
- : 		CleanupMode cleanupMode = determineCleanupModeForParameter(parameterContext);
- : 		TempDirFactory factory = determineTempDirFactoryForParameter(parameterContext);
- : 		return getPathOrFile(parameterType, parameterContext, factory, cleanupMode, extensionContext);
+ 170: 		TempDir tempDir = findAnnotationOnParameter(parameterContext);
+ 171: 		return getPathOrFile(parameterType, parameterContext, extensionContext, tempDir);
  172: 	}
  173: 
- : 	private CleanupMode determineCleanupModeForField(Field field) {
- : 		TempDir tempDir = findAnnotation(field, TempDir.class).orElseThrow(
+ 174: 	private static TempDir findAnnotationOnField(Field field) {
+ 175: 		return findAnnotation(field, TempDir.class).orElseThrow(
  176: 			() -> new JUnitException("Field " + field + " must be annotated with @TempDir"));
- : 		return determineCleanupMode(tempDir);
  177: 	}
  178: 
- : 	private CleanupMode determineCleanupModeForParameter(ParameterContext parameterContext) {
- : 		TempDir tempDir = parameterContext.findAnnotation(TempDir.class).orElseThrow(() -> new JUnitException(
+ 179: 	private static TempDir findAnnotationOnParameter(ParameterContext parameterContext) {
+ 180: 		return parameterContext.findAnnotation(TempDir.class).orElseThrow(() -> new JUnitException(
  181: 			"Parameter " + parameterContext.getParameter() + " must be annotated with @TempDir"));
- : 		return determineCleanupMode(tempDir);
  182: 	}
  183: 
- : 	private CleanupMode determineCleanupMode(TempDir tempDir) {
- : 		CleanupMode cleanupMode = tempDir.cleanup();
+ 184: 	private CleanupMode determineCleanupMode(TempDir annotation) {
+ 185: 		var cleanupMode = annotation.cleanup();
  186: 		return cleanupMode == DEFAULT ? this.configuration.getDefaultTempDirCleanupMode() : cleanupMode;
  187: 	}
  188: 
- : 	private TempDirFactory determineTempDirFactoryForField(Field field) {
- : 		TempDir tempDir = findAnnotation(field, TempDir.class).orElseThrow(
- : 			() -> new JUnitException("Field " + field + " must be annotated with @TempDir"));
- : 		return determineTempDirFactory(tempDir);
- : 	}
- : 
- : 	private TempDirFactory determineTempDirFactoryForParameter(ParameterContext parameterContext) {
- : 		TempDir tempDir = parameterContext.findAnnotation(TempDir.class).orElseThrow(() -> new JUnitException(
- : 			"Parameter " + parameterContext.getParameter() + " must be annotated with @TempDir"));
- : 		return determineTempDirFactory(tempDir);
+ 189: 	private Supplier<TempDirDeletionStrategy> determineDeletionStrategy(TempDir annotation) {
+ 190: 		var strategyClass = annotation.deletionStrategy();
+ 191: 		return strategyClass == TempDirDeletionStrategy.class //
+ 192: 				? this.configuration.getDefaultTempDirDeletionStrategySupplier() //
+ 193: 				: () -> ReflectionSupport.newInstance(strategyClass);
  194: 	}
  195: 
  196: 	private TempDirFactory determineTempDirFactory(TempDir tempDir) {
  197: 		Class<? extends TempDirFactory> factory = tempDir.factory();
  198: 
  199: 		return factory == TempDirFactory.class //
  200: 				? this.configuration.getDefaultTempDirFactorySupplier().get()
  201: 				: ReflectionSupport.newInstance(factory);
  202: 	}
  203: 
  204: 	private static void assertNonFinalField(Field field) {
  205: 		if (ModifierSupport.isFinal(field)) {
  206: 			throw new ExtensionConfigurationException("@TempDir field [" + field + "] must not be declared as final.");
  207: 		}
  208: 	}
  209: 
  210: 	private static void assertSupportedType(String target, Class<?> type) {
  211: 		if (type != Path.class && type != File.class) {
  212: 			throw new ExtensionConfigurationException("Can only resolve @TempDir " + target + " of type "
  213: 					+ Path.class.getName() + " or " + File.class.getName() + " but was: " + type.getName());
  214: 		}
  215: 	}
  216: 
+ 217: 	private Object getPathOrFile(Class<?> elementType, AnnotatedElementContext elementContext,
+ 218: 			ExtensionContext extensionContext, TempDir tempDir) {
+ 219: 		TempDirFactory factory = determineTempDirFactory(tempDir);
+ 220: 		Cleanup cleanup = new Cleanup(determineCleanupMode(tempDir), determineDeletionStrategy(tempDir));
+ 221: 		return getPathOrFile(elementType, elementContext, factory, cleanup, extensionContext);
+ 222: 	}
+ 223: 
  224: 	private static Object getPathOrFile(Class<?> elementType, AnnotatedElementContext elementContext,
- : 			TempDirFactory factory, CleanupMode cleanupMode, ExtensionContext extensionContext) {
+ 225: 			TempDirFactory factory, Cleanup cleanup, ExtensionContext extensionContext) {
  226: 
  227: 		Path path = extensionContext.getStore(NAMESPACE.append(elementContext)) //
  228: 				.computeIfAbsent(KEY,
- : 					__ -> createTempDir(factory, cleanupMode, elementType, elementContext, extensionContext),
+ 229: 					__ -> createTempDir(factory, cleanup, elementType, elementContext, extensionContext),
  230: 					CloseablePath.class) //
  231: 				.get();
  232: 
  233: 		return (elementType == Path.class) ? path : path.toFile();
  234: 	}
  235: 
- : 	static CloseablePath createTempDir(TempDirFactory factory, CleanupMode cleanupMode, Class<?> elementType,
+ 236: 	static CloseablePath createTempDir(TempDirFactory factory, Cleanup cleanup, Class<?> elementType,
  237: 			AnnotatedElementContext elementContext, ExtensionContext extensionContext) {
  238: 
  239: 		try {
- : 			return new CloseablePath(factory, cleanupMode, elementType, elementContext, extensionContext);
+ 240: 			return new CloseablePath(factory, cleanup, elementType, elementContext, extensionContext);
  241: 		}
  242: 		catch (Exception ex) {
  243: 			throw new ExtensionConfigurationException("Failed to create default temp directory", ex);
  244: 		}
  245: 	}
  246: 
  247: 	private static boolean selfOrChildFailed(ExtensionContext context) {
  248: 		return context.getExecutionException().isPresent() //
  249: 				|| getContextSpecificStore(context).getOrDefault(CHILD_FAILED, Boolean.class, false);
  250: 	}
  251: 
  252: 	private static ExtensionContext.Store getContextSpecificStore(ExtensionContext context) {
  253: 		return context.getStore(NAMESPACE.append(context));
  254: 	}
  255: 
  256: 	@SuppressWarnings("deprecation")
  257: 	static class CloseablePath implements Store.CloseableResource, AutoCloseable {
  258: 
- : 		private static final Logger LOGGER = LoggerFactory.getLogger(CloseablePath.class);
- : 
- : 		private final Path dir;
+ 259: 		private final @Nullable Path dir;
  260: 		private final TempDirFactory factory;
- : 		private final CleanupMode cleanupMode;
- : 		private final AnnotatedElement annotatedElement;
+ 261: 		private final Cleanup cleanup;
+ 262: 		private final AnnotatedElementContext elementContext;
  263: 		private final ExtensionContext extensionContext;
  264: 
- : 		private CloseablePath(TempDirFactory factory, CleanupMode cleanupMode, Class<?> elementType,
+ 265: 		private CloseablePath(TempDirFactory factory, Cleanup cleanup, Class<?> elementType,
  266: 				AnnotatedElementContext elementContext, ExtensionContext extensionContext) throws Exception {
  267: 			this.dir = factory.createTempDirectory(elementContext, extensionContext);
  268: 			this.factory = factory;
- : 			this.cleanupMode = cleanupMode;
- : 			this.annotatedElement = elementContext.getAnnotatedElement();
+ 269: 			this.cleanup = cleanup;
+ 270: 			this.elementContext = elementContext;
  271: 			this.extensionContext = extensionContext;
  272: 
  273: 			if (this.dir == null || !Files.isDirectory(this.dir)) {
  274: 				close();
  275: 				throw new PreconditionViolationException("temp directory must be a directory");
  276: 			}
  277: 
  278: 			if (elementType == File.class && !this.dir.getFileSystem().equals(FileSystems.getDefault())) {
  279: 				close();
  280: 				throw new PreconditionViolationException(
  281: 					"temp directory with non-default file system cannot be injected into " + File.class.getName()
  282: 							+ " target");
  283: 			}
  284: 		}
  285: 
  286: 		Path get() {
- : 			return this.dir;
+ 287: 			return requireNonNull(this.dir);
  288: 		}
  289: 
  290: 		@Override
  291: 		public void close() throws IOException {
  292: 			try {
- : 				if (this.cleanupMode == NEVER
- : 						|| (this.cleanupMode == ON_SUCCESS && selfOrChildFailed(this.extensionContext))) {
- : 					LOGGER.info(() -> "Skipping cleanup of temp dir %s for %s due to CleanupMode.%s.".formatted(
- : 						this.dir, descriptionFor(this.annotatedElement), this.cleanupMode.name()));
- : 					return;
- : 				}
- : 
- : 				FileOperations fileOperations = this.extensionContext.getStore(NAMESPACE) //
- : 						.getOrDefault(FILE_OPERATIONS_KEY, FileOperations.class, FileOperations.DEFAULT);
- : 				FileOperations loggingFileOperations = file -> {
- : 					LOGGER.trace(() -> "Attempting to delete " + file);
- : 					try {
- : 						fileOperations.delete(file);
- : 						LOGGER.trace(() -> "Successfully deleted " + file);
- : 					}
- : 					catch (IOException e) {
- : 						LOGGER.trace(e, () -> "Failed to delete " + file);
- : 						throw e;
- : 					}
- : 				};
- : 
- : 				LOGGER.trace(() -> "Cleaning up temp dir " + this.dir);
- : 				SortedMap<Path, IOException> failures = deleteAllFilesAndDirectories(loggingFileOperations);
- : 				if (!failures.isEmpty()) {
- : 					throw createIOExceptionWithAttachedFailures(failures);
+ 293: 				if (this.dir != null) {
+ 294: 					this.cleanup.run(this.dir, this.elementContext, this.extensionContext);
  295: 				}
  296: 			}
  297: 			finally {
  298: 				this.factory.close();
  299: 			}
  300: 		}
- : 
- : 		/**
- : 		 * @since 5.12
- : 		 */
- : 		private static String descriptionFor(AnnotatedElement annotatedElement) {
- : 			if (annotatedElement instanceof Field field) {
- : 				return "field " + field.getDeclaringClass().getSimpleName() + "." + field.getName();
- : 			}
- : 			if (annotatedElement instanceof Parameter parameter) {
- : 				Executable executable = parameter.getDeclaringExecutable();
- : 				return "parameter '" + parameter.getName() + "' in " + descriptionFor(executable);
- : 			}
- : 			throw new IllegalStateException("Unsupported AnnotatedElement type for @TempDir: " + annotatedElement);
- : 		}
- : 
- : 		/**
- : 		 * @since 5.12
- : 		 */
- : 		private static String descriptionFor(Executable executable) {
- : 			boolean isConstructor = executable instanceof Constructor<?>;
- : 			String type = isConstructor ? "constructor" : "method";
- : 			String name = isConstructor ? executable.getDeclaringClass().getSimpleName() : executable.getName();
- : 			return "%s %s(%s)".formatted(type, name,
- : 				ClassUtils.nullSafeToString(Class::getSimpleName, executable.getParameterTypes()));
- : 		}
- : 
- : 		private SortedMap<Path, IOException> deleteAllFilesAndDirectories(FileOperations fileOperations)
- : 				throws IOException {
- : 
- : 			Path rootDir = this.dir;
- : 			if (rootDir == null || Files.notExists(rootDir)) {
- : 				return Collections.emptySortedMap();
- : 			}
- : 
- : 			SortedMap<Path, IOException> failures = new TreeMap<>();
- : 			Set<Path> retriedPaths = new HashSet<>();
- : 			Path rootRealPath = rootDir.toRealPath();
- : 
- : 			tryToResetPermissions(rootDir);
- : 			Files.walkFileTree(rootDir, new SimpleFileVisitor<Path>() {
- : 
- : 				@Override
- : 				public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) throws IOException {
- : 					LOGGER.trace(() -> "preVisitDirectory: " + dir);
- : 					if (isLinkWithTargetOutsideTempDir(dir)) {
- : 						warnAboutLinkWithTargetOutsideTempDir("link", dir);
- : 						delete(dir);
- : 						return SKIP_SUBTREE;
- : 					}
- : 					if (!dir.equals(rootDir)) {
- : 						tryToResetPermissions(dir);
- : 					}
- : 					return CONTINUE;
- : 				}
- : 
- : 				@Override
- : 				public FileVisitResult visitFileFailed(Path file, IOException exc) {
- : 					LOGGER.trace(exc, () -> "visitFileFailed: " + file);
- : 					if (exc instanceof NoSuchFileException && !Files.exists(file, LinkOption.NOFOLLOW_LINKS)) {
- : 						return CONTINUE;
- : 					}
- : 					// IOException includes `AccessDeniedException` thrown by non-readable or non-executable flags
- : 					resetPermissionsAndTryToDeleteAgain(file, exc);
- : 					return CONTINUE;
- : 				}
- : 
- : 				@Override
- : 				public FileVisitResult visitFile(Path file, BasicFileAttributes attributes) throws IOException {
- : 					LOGGER.trace(() -> "visitFile: " + file);
- : 					if (Files.isSymbolicLink(file) && isLinkWithTargetOutsideTempDir(file)) {
- : 						warnAboutLinkWithTargetOutsideTempDir("symbolic link", file);
- : 					}
- : 					delete(file);
- : 					return CONTINUE;
- : 				}
- : 
- : 				@Override
- : 				public FileVisitResult postVisitDirectory(Path dir, IOException exc) {
- : 					LOGGER.trace(exc, () -> "postVisitDirectory: " + dir);
- : 					delete(dir);
- : 					return CONTINUE;
- : 				}
- : 
- : 				private boolean isLinkWithTargetOutsideTempDir(Path path) {
- : 					// While `Files.walkFileTree` does not follow symbolic links, it may follow other links
- : 					// such as "junctions" on Windows
- : 					try {
- : 						return !path.toRealPath().startsWith(rootRealPath);
- : 					}
- : 					catch (IOException e) {
- : 						LOGGER.trace(e,
- : 							() -> "Failed to determine real path for " + path + "; assuming it is not a link");
- : 						return false;
- : 					}
- : 				}
- : 
- : 				private void warnAboutLinkWithTargetOutsideTempDir(String linkType, Path file) throws IOException {
- : 					Path realPath = file.toRealPath();
- : 					LOGGER.warn(() -> """
- : 							Deleting %s from location inside of temp dir (%s) \
- : 							to location outside of temp dir (%s) but not the target file/directory""".formatted(
- : 						linkType, file, realPath));
- : 				}
- : 
- : 				private void delete(Path path) {
- : 					try {
- : 						fileOperations.delete(path);
- : 					}
- : 					catch (NoSuchFileException ignore) {
- : 						// ignore
- : 					}
- : 					catch (DirectoryNotEmptyException exception) {
- : 						failures.put(path, exception);
- : 					}
- : 					catch (IOException exception) {
- : 						// IOException includes `AccessDeniedException` thrown by non-readable or non-executable flags
- : 						resetPermissionsAndTryToDeleteAgain(path, exception);
- : 					}
- : 				}
- : 
- : 				private void resetPermissionsAndTryToDeleteAgain(Path path, IOException exception) {
- : 					boolean notYetRetried = retriedPaths.add(path);
- : 					if (notYetRetried) {
- : 						try {
- : 							tryToResetPermissions(path);
- : 							if (Files.isDirectory(path)) {
- : 								Files.walkFileTree(path, this);
- : 							}
- : 							else {
- : 								fileOperations.delete(path);
- : 							}
- : 						}
- : 						catch (Exception suppressed) {
- : 							exception.addSuppressed(suppressed);
- : 							failures.put(path, exception);
- : 						}
- : 					}
- : 					else {
- : 						failures.put(path, exception);
- : 					}
- : 				}
- : 			});
- : 			return failures;
- : 		}
- : 
- : 		@SuppressWarnings("ResultOfMethodCallIgnored")
- : 		private static void tryToResetPermissions(Path path) {
- : 			File file;
- : 			try {
- : 				file = path.toFile();
- : 			}
- : 			catch (UnsupportedOperationException ignore) {
- : 				// Might happen when the `TempDirFactory` uses a custom `FileSystem`
- : 				return;
- : 			}
- : 			file.setReadable(true);
- : 			file.setWritable(true);
- : 			if (Files.isDirectory(path)) {
- : 				file.setExecutable(true);
- : 			}
- : 			DosFileAttributeView dos = Files.getFileAttributeView(path, DosFileAttributeView.class);
- : 			if (dos != null) {
- : 				try {
- : 					dos.setReadOnly(false);
- : 				}
- : 				catch (IOException ignore) {
- : 					// nothing we can do
- : 				}
- : 			}
- : 		}
- : 
- : 		private IOException createIOExceptionWithAttachedFailures(SortedMap<Path, IOException> failures) {
- : 			Path emptyPath = Path.of("");
- : 			String joinedPaths = failures.keySet().stream() //
- : 					.map(this::tryToDeleteOnExit) //
- : 					.map(this::relativizeSafely) //
- : 					.map(path -> emptyPath.equals(path) ? "<root>" : path.toString()) //
- : 					.collect(joining(", "));
- : 			IOException exception = new IOException("Failed to delete temp directory " + this.dir.toAbsolutePath()
- : 					+ ". The following paths could not be deleted (see suppressed exceptions for details): "
- : 					+ joinedPaths);
- : 			failures.values().forEach(exception::addSuppressed);
- : 			return exception;
- : 		}
- : 
- : 		@SuppressWarnings("EmptyCatch")
- : 		private Path tryToDeleteOnExit(Path path) {
- : 			try {
- : 				path.toFile().deleteOnExit();
- : 			}
- : 			catch (UnsupportedOperationException ignore) {
- : 			}
- : 			return path;
- : 		}
- : 
- : 		private Path relativizeSafely(Path path) {
- : 			try {
- : 				return this.dir.relativize(path);
- : 			}
- : 			catch (IllegalArgumentException e) {
- : 				return path;
- : 			}
- : 		}
- : 	}
- : 
- : 	interface FileOperations {
- : 
- : 		FileOperations DEFAULT = Files::delete;
- : 
- : 		void delete(Path path) throws IOException;
- : 
  301: 	}
  302: 
  303: 	private record FieldContext(Field field) implements AnnotatedElementContext {
  304: 
  305: 		private FieldContext(Field field) {
  306: 			this.field = Preconditions.notNull(field, "field must not be null");
  307: 		}
  308: 
  309: 		@Override
  310: 		public AnnotatedElement getAnnotatedElement() {
  311: 			return this.field;
  312: 		}
  313:
```

**The reviewer's comment:**

> The new getPathOrFile method consolidates the logic for determining cleanup and factory, making the code more modular and easier to test.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 34. `qwen__qwen3-coder-30b-a3b-instruct__checkstyle__checkstyle__20554__unmatched_model__5`

**Arm:** `qwen`  •  **File:** `src/xdocs-examples/java/com/puppycrawl/tools/checkstyle/checks/TodoCommentCheckExamplesTest.java`  •  **comment on line 47**  •  [PR #20554](https://github.com/checkstyle/checkstyle/pull/20554)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  24: import org.junit.jupiter.api.Test;
  25: 
  26: import com.puppycrawl.tools.checkstyle.AbstractExamplesModuleTestSupport;
  27: 
  28: public class TodoCommentCheckExamplesTest extends AbstractExamplesModuleTestSupport {
  29:     @Override
  30:     public String getPackageLocation() {
  31:         return "com/puppycrawl/tools/checkstyle/checks/todocomment";
  32:     }
  33: 
  34:     @Test
  35:     public void testExample1() throws Exception {
  36:         final String[] expected = {
- :             "16:14: " + getCheckMessage(MSG_KEY, "TODO:"),
+ 37:             "24:7: " + getCheckMessage(MSG_KEY, "TODO:"),
  38:         };
  39: 
  40:         verifyWithInlineConfigParser(getPath("Example1.java"), expected);
  41:     }
  42: 
  43:     @Test
  44:     public void testExample2() throws Exception {
  45:         final String[] expected = {
  46:             "1:3: " + getCheckMessage(MSG_KEY, "(?i)(TODO)|(FIXME)"),
- :             "20:14: " + getCheckMessage(MSG_KEY, "(?i)(TODO)|(FIXME)"),
- :             "22:14: " + getCheckMessage(MSG_KEY, "(?i)(TODO)|(FIXME)"),
- :             "24:14: " + getCheckMessage(MSG_KEY, "(?i)(TODO)|(FIXME)"),
+ 47:             "27:7: " + getCheckMessage(MSG_KEY, "(?i)(TODO)|(FIXME)"),
+ 48:             "31:7: " + getCheckMessage(MSG_KEY, "(?i)(TODO)|(FIXME)"),
+ 49:             "35:7: " + getCheckMessage(MSG_KEY, "(?i)(TODO)|(FIXME)"),
  50:         };
  51: 
  52:         verifyWithInlineConfigParser(getPath("Example2.java"), expected);
  53:     }
  54: 
  55:     @Test
  56:     public void testExample3() throws Exception {
  57:         final String[] expected = {
- :             "17:3: Comment uses box-like repetitive character pattern.",
- :             "26:5: Comment uses box-like repetitive character pattern.",
- :             "32:5: Comment uses box-like repetitive character pattern.",
- :             "38:5: Comment uses box-like repetitive character pattern.",
+ 58:             "18:3: Comment uses box-like repetitive character pattern.",
+ 59:             "27:5: Comment uses box-like repetitive character pattern.",
+ 60:             "42:5: Comment uses box-like repetitive character pattern.",
+ 61:             "47:5: Comment uses box-like repetitive character pattern.",
  62:         };
  63: 
  64:         verifyWithInlineConfigParser(getPath("Example3.java"), expected);
  65:     }
  66: }
```

**The reviewer's comment:**

> Multiple line numbers in expected output have been shifted (14->7, 20->27, 22->31, 24->35), indicating the test file content has changed. This could cause test failures if the actual file structure doesn't match these new line numbers.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 35. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5135__unmatched_model__8`

**Arm:** `qwen`  •  **File:** `junit-platform-engine/src/main/java/org/junit/platform/engine/support/hierarchical/WorkerThreadPoolHierarchicalTestExecutorService.java`  •  **comment on line 677**  •  [PR #5135](https://github.com/junit-team/junit5/pull/5135)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  643: 				catch (Exception ex) {
  644: 					throw throwAsUncheckedException(ex);
  645: 				}
  646: 			});
  647: 		}
  648: 
  649: 	}
  650: 
  651: 	private enum BlockingMode {
  652: 		NON_BLOCKING, BLOCKING
  653: 	}
  654: 
  655: 	private static class WorkQueue implements Iterable<WorkQueue.Entry> {
- : 		private final Set<Entry> queue = new ConcurrentSkipListSet<>();
+ 656: 
+ 657: 		private final Set<Entry> queue = new ConcurrentSkipListSet<>(Entry.QUEUE_COMPARATOR);
  658: 
  659: 		Entry add(TestTask task, int index) {
- : 			Entry entry = createEntry(task, index);
+ 660: 			Entry entry = new Entry(task, index);
  661: 			LOGGER.trace(() -> "forking: " + entry.task);
  662: 			return doAdd(entry);
  663: 		}
  664: 
- : 		Entry createEntry(TestTask task, int index) {
- : 			var uniqueId = task.getTestDescriptor().getUniqueId();
- : 			return new Entry(uniqueId, task, new CompletableFuture<>(), index);
- : 		}
- : 
  665: 		void addAll(Collection<Entry> entries) {
  666: 			entries.forEach(this::doAdd);
  667: 		}
  668: 
  669: 		void reAdd(Entry entry) {
  670: 			LOGGER.trace(() -> "re-enqueuing: " + entry.task);
  671: 			doAdd(entry);
  672: 		}
  673: 
  674: 		private Entry doAdd(Entry entry) {
  675: 			var added = queue.add(entry);
  676: 			if (!added) {
  677: 				throw new IllegalStateException("Could not add entry to the queue for task: " + entry.task);
```

**The reviewer's comment:**

> The IllegalStateException thrown when an entry cannot be added to the queue could cause test execution to fail unexpectedly. Consider a more graceful handling or logging approach.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 36. `qwen__qwen3-coder-30b-a3b-instruct__mockito__mockito__2807__unmatched_model__14`

**Arm:** `qwen`  •  **File:** `src/main/java/org/mockito/internal/matchers/InstanceOf.java`  •  **comment on line 34**  •  [PR #2807](https://github.com/mockito/mockito/pull/2807)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  1: /*
  2:  * Copyright (c) 2007 Mockito contributors
  3:  * This program is made available under the terms of the MIT License.
  4:  */
  5: package org.mockito.internal.matchers;
  6: 
  7: import java.io.Serializable;
  8: 
  9: import org.mockito.ArgumentMatcher;
  10: import org.mockito.internal.util.Primitives;
  11: 
  12: public class InstanceOf implements ArgumentMatcher<Object>, Serializable {
  13: 
- :     private final Class<?> clazz;
+ 14:     final Class<?> clazz;
  15:     private final String description;
  16: 
  17:     public InstanceOf(Class<?> clazz) {
  18:         this(clazz, "isA(" + clazz.getCanonicalName() + ")");
  19:     }
  20: 
  21:     public InstanceOf(Class<?> clazz, String describedAs) {
  22:         this.clazz = clazz;
  23:         this.description = describedAs;
  24:     }
  25: 
  26:     @Override
  27:     public boolean matches(Object actual) {
  28:         return (actual != null)
  29:                 && (Primitives.isAssignableFromWrapper(actual.getClass(), clazz)
  30:                         || clazz.isAssignableFrom(actual.getClass()));
  31:     }
  32: 
+ 33:     @Override
+ 34:     public Class<?> type() {
+ 35:         return clazz;
+ 36:     }
+ 37: 
  38:     @Override
  39:     public String toString() {
  40:         return description;
  41:     }
  42: 
  43:     public static class VarArgAware extends InstanceOf implements VarargMatcher {
  44: 
  45:         public VarArgAware(Class<?> clazz) {
  46:             super(clazz);
  47:         }
  48: 
  49:         public VarArgAware(Class<?> clazz, String describedAs) {
  50:             super(clazz, describedAs);
  51:         }
+ 52: 
+ 53:         @Override
+ 54:         public Class<?> type() {
+ 55:             return clazz;
+ 56:         }
  57:     }
  58: }
```

**The reviewer's comment:**

> Missing javadoc for the new type() method. Consider adding documentation explaining its purpose and usage.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 37. `qwen__qwen3-coder-30b-a3b-instruct__checkstyle__checkstyle__20717__unmatched_model__4`

**Arm:** `qwen`  •  **File:** `src/test/java/com/puppycrawl/tools/checkstyle/checks/design/InnerTypeLastCheckTest.java`  •  **comment on line 163**  •  [PR #20717](https://github.com/checkstyle/checkstyle/pull/20717)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  131:     @Test
  132:     public void testGetAcceptableTokens() {
  133:         final InnerTypeLastCheck obj = new InnerTypeLastCheck();
  134:         final int[] expected = {
  135:             TokenTypes.CLASS_DEF,
  136:             TokenTypes.INTERFACE_DEF,
  137:             TokenTypes.RECORD_DEF,
  138:         };
  139:         assertWithMessage("Default acceptable tokens are invalid")
  140:             .that(obj.getAcceptableTokens())
  141:             .isEqualTo(expected);
  142:     }
  143: 
+ 144:     @Test
+ 145:     public void testInnerTypeLastCompactSourceFile() throws Exception {
+ 146:         final String[] expected = {
+ 147:             "12:1: " + getCheckMessage(MSG_KEY),
+ 148:         };
+ 149:         verifyWithInlineConfigParser(
+ 150:                 getNonCompilablePath("compact/InputInnerTypeLastCompactSourceFile.java"), expected);
+ 151:     }
+ 152: 
+ 153:     @Test
+ 154:     public void testInnerTypeLastCompactSourceFileNested() throws Exception {
+ 155:         final String[] expected = {
+ 156:             "15:5: " + getCheckMessage(MSG_KEY),
+ 157:         };
+ 158:         verifyWithInlineConfigParser(
+ 159:                 getNonCompilablePath("compact/InputInnerTypeLastCompactSourceFileNested.java"),
+ 160:                 expected);
+ 161:     }
+ 162: 
+ 163:     @Test
+ 164:     public void testInnerTypeLastEmpty() throws Exception {
+ 165:         final String[] expected = CommonUtil.EMPTY_STRING_ARRAY;
+ 166:         verifyWithInlineConfigParser(
+ 167:                 getNonCompilablePath("InputInnerTypeLastEmpty.java"), expected);
+ 168:     }
  169: }
```

**The reviewer's comment:**

> Consider adding a javadoc comment to explain what this test verifies

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 38. `qwen__qwen3-coder-30b-a3b-instruct__mockito__mockito__2650__unmatched_model__18`

**Arm:** `qwen`  •  **File:** `src/test/java/org/mockitousage/strictness/StrictnessMockAnnotationTest.java`  •  **comment on line 31**  •  [PR #2650](https://github.com/mockito/mockito/pull/2650)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

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

**The reviewer's comment:**

> The test calls ProductionCode.simpleMethod(lenientMock, "3") but does not verify that the method was actually called or that the stubbing worked as expected. This could lead to false positives in the test.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 39. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5042__unmatched_model__17`

**Arm:** `qwen`  •  **File:** `junit-platform-commons/src/main/java/org/junit/platform/commons/util/ModuleUtils.java`  •  **comment on line 261**  •  [PR #5042](https://github.com/junit-team/junit5/pull/5042)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  243: 
  244: 		ModuleReferenceClassScanner(ClassFilter classFilter, ClassLoader classLoader) {
  245: 			this.classFilter = classFilter;
  246: 			this.classLoader = classLoader;
  247: 		}
  248: 
  249: 		/**
  250: 		 * Scan module reference for classes that potentially contain testable methods.
  251: 		 */
  252: 		List<Class<?>> scan(ModuleReference reference) {
  253: 			try (ModuleReader reader = reference.open()) {
  254: 				try (Stream<String> names = reader.list()) {
  255: 					// @formatter:off
- : 					return names.filter(name -> name.endsWith(".class"))
- : 							.map(this::className)
+ 256: 					return names.filter(ClasspathFilters::isClassOrSourceFileName)
+ 257: 							.map(DefaultClasspathScanner::determineSimpleClassName)
+ 258: 							.map(name -> name.replace('/', '.'))
  259: 							.filter(name -> !"module-info".equals(name))
+ 260: 							.filter(name -> !name.endsWith("package-info"))
  261: 							.filter(classFilter::match)
  262: 							.<Class<?>> map(this::loadClassUnchecked)
  263: 							.filter(classFilter::match)
  264: 							.toList();
  265: 					// @formatter:on
  266: 				}
  267: 			}
  268: 			catch (IOException e) {
  269: 				throw new JUnitException("Failed to read contents of " + reference + ".", e);
  270: 			}
  271: 		}
  272: 
- : 		/**
- : 		 * Convert resource name to binary class name.
- : 		 */
- : 		private String className(String resourceName) {
- : 			resourceName = resourceName.substring(0, resourceName.length() - 6); // 6 = ".class".length()
- : 			resourceName = resourceName.replace('/', '.');
- : 			return resourceName;
- : 		}
- : 
  273: 		/**
  274: 		 * Load class by its binary name.
  275: 		 *
  276: 		 * @see ClassLoader#loadClass(String)
  277: 		 */
  278: 		private Class<?> loadClassUnchecked(String binaryName) {
  279: 			try {
  280: 				return classLoader.loadClass(binaryName);
  281: 			}
  282: 			catch (ClassNotFoundException e) {
  283: 				throw new JUnitException("Failed to load class with name '" + binaryName + "'.", e);
  284: 			}
  285: 		}
```

**The reviewer's comment:**

> The classFilter::match is now applied twice - once before and once after loading the class. This could impact performance and may be redundant. Verify if both filters are necessary.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 40. `qwen__qwen3-coder-30b-a3b-instruct__checkstyle__checkstyle__20351__unmatched_model__16`

**Arm:** `qwen`  •  **File:** `src/test/resources/com/puppycrawl/tools/checkstyle/checks/javadoc/javadoctype/InputJavadocTypeRecordParamDescriptionWithAngularTags.java`  •  **comment on line 66**  •  [PR #20351](https://github.com/checkstyle/checkstyle/pull/20351)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  53: 
  54: // violation 3 lines below 'Unused @param tag for \'<P>\'.'
  55: /**
  56:  * @param <T>
  57:  * @param    <P>     stuff <><><<stuff></></></> stuff
  58:  */
  59: record Record5<T, U>() {} // violation, 'Type Javadoc comment is missing @param <U> tag.'
  60: 
  61: // violation 3 lines below 'Unused @param tag for \'region\'.'
  62: /**
  63:  *
  64:  * @param region [(<>{@code stuff<stuff🐦‍🔥>🐦‍🔥&lt;stuff&gt;}</>)]{@code {&lt;stuff&gt;}}
  65:  */
- : record Record6(int a) {} // violation, 'Type Javadoc comment is missing @param a tag.'
+ 66: record Record6(int a) {} // violation, 'Type Javadoc comment is missing @param 'a' tag.'
  67: 
  68: /**
  69:  *
  70:  * @param <T>
  71:  * @param a 🐦‍🔥<><🐦‍🔥><<stuff></></></> stuff🐦‍🔥
  72:  * @param b
  73:  */
  74: record Record7<T>(int a, int b) {}
  75: 
  76: // violation 4 lines below 'Unused @param tag for \'e\'.'
  77: /**
  78:  * @param a <<></>></><<></>></>
  79:  * @param b stuff<stuff>:<>:<>:<🐦‍🔥<<🐦‍🔥>>🐦‍🔥>
  80:  * @param e [(<>{@code stuff<stuff🐦[(‍{🔥}])>🐦‍🔥&lt;stuff&gt;}</>)]{@code {&lt;stuff&gt;}}
  81:  */
- : record Record8(int a, int b, int c) { // violation, 'Type Javadoc comment is missing @param c tag.'
+ 82: record Record8(int a, int b, int c) { // violation, 'missing @param 'c' tag.'
  83: }
  84: 
  85: /**
  86:  *
  87:  * @param a [(<>{@code stuff<stuff🐦‍🔥>🐦‍🔥&lt;stuff&gt;}</>)]
  88:  */
  89: record Record9(int a) {}
  90: 
  91: /**
  92:  *
  93:  * @param a <><><><><><><><>
  94:  * @param b >><>>><><><<<><<
  95:  * @param c {@code <{[(<stu<f>f>)]}>}
```

**The reviewer's comment:**

> Inconsistent phrasing in violation message: 'Type Javadoc comment is missing @param 'a' tag.' vs previous examples using 'missing @param 'a' tag.'

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 41. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5379__unmatched_model__36`

**Arm:** `qwen`  •  **File:** `junit-jupiter-engine/src/main/java/org/junit/jupiter/engine/Constants.java`  •  **comment on line 565**  •  [PR #5379](https://github.com/junit-team/junit5/pull/5379)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  143: 	 * <li>{@code *.MyCondition}: deactivates every condition whose simple class name is
  144: 	 * exactly {@code MyCondition}.
  145: 	 * <li>{@code *System*}: deactivates every condition whose FQCN contains
  146: 	 * {@code System}.
  147: 	 * <li>{@code *System*, *Dev*}: deactivates every condition whose FQCN contains
  148: 	 * {@code System} or {@code Dev}.
  149: 	 * <li>{@code org.example.MyCondition, org.example.TheirCondition}: deactivates
  150: 	 * conditions whose FQCN is exactly {@code org.example.MyCondition} or
  151: 	 * {@code org.example.TheirCondition}.
  152: 	 * </ul>
  153: 	 *
  154: 	 * @see #DEACTIVATE_ALL_CONDITIONS_PATTERN
  155: 	 * @see org.junit.jupiter.api.extension.ExecutionCondition
+ 156: 	 * @deprecated Please use
+ 157: 	 * {@link org.junit.jupiter.api.Constants#DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME}
+ 158: 	 * instead.
  159: 	 */
- : 	public static final String DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME = JupiterConfiguration.DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME;
+ 160: 	@API(status = DEPRECATED, since = "6.1")
+ 161: 	@Deprecated(forRemoval = true, since = "6.1")
+ 162: 	public static final String DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME;
  163: 
  164: 	/**
  165: 	 * Wildcard pattern which signals that all conditions should be deactivated: {@value}
  166: 	 *
  167: 	 * @see #DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME
  168: 	 * @see org.junit.jupiter.api.extension.ExecutionCondition
+ 169: 	 * @deprecated Please use
+ 170: 	 * {@link org.junit.jupiter.api.Constants#DEACTIVATE_ALL_CONDITIONS_PATTERN}
+ 171: 	 * instead.
  172: 	 */
- : 	public static final String DEACTIVATE_ALL_CONDITIONS_PATTERN = ClassNamePatternFilterUtils.ALL_PATTERN;
+ 173: 	@API(status = DEPRECATED, since = "6.1")
+ 174: 	@Deprecated(forRemoval = true, since = "6.1")
+ 175: 	public static final String DEACTIVATE_ALL_CONDITIONS_PATTERN = org.junit.jupiter.api.Constants.DEACTIVATE_ALL_CONDITIONS_PATTERN;
  176: 
  177: 	/**
  178: 	 * Property name used to set the default display name generator class name: {@value}
  179: 	 *
  180: 	 * @see DisplayNameGenerator#DEFAULT_GENERATOR_PROPERTY_NAME
+ 181: 	 * @deprecated Please use
+ 182: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME}
+ 183: 	 * instead.
  184: 	 */
- : 	public static final String DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME = DisplayNameGenerator.DEFAULT_GENERATOR_PROPERTY_NAME;
+ 185: 	@API(status = DEPRECATED, since = "6.1")
+ 186: 	@Deprecated(forRemoval = true, since = "6.1")
+ 187: 	public static final String DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME;
  188: 
  189: 	/**
  190: 	 * Property name used to enable auto-detection and registration of extensions via
  191: 	 * Java's {@link java.util.ServiceLoader} mechanism: {@value}
  192: 	 *
  193: 	 * <p>The default behavior is not to perform auto-detection.
+ 194: 	 * @deprecated Please use
+ 195: 	 * {@link org.junit.jupiter.api.Constants#EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME}
+ 196: 	 * instead.
  197: 	 */
- : 	public static final String EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME = JupiterConfiguration.EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME;
+ 198: 	@API(status = DEPRECATED, since = "6.1")
+ 199: 	@Deprecated(forRemoval = true, since = "6.1")
+ 200: 	public static final String EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME = org.junit.jupiter.api.Constants.EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME;
  201: 
  202: 	/**
  203: 	 * Property name used to enable dumping the stack of all
  204: 	 * {@linkplain Thread threads} to {@code System.out} when a timeout has occurred.
  205: 	 *
  206: 	 * <p>This behavior is disabled by default.
  207: 	 *
  208: 	 * @since 5.12
  209: 	 */
  210: 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String EXTENSIONS_TIMEOUT_THREAD_DUMP_ENABLED_PROPERTY_NAME = JupiterConfiguration.EXTENSIONS_TIMEOUT_THREAD_DUMP_ENABLED_PROPERTY_NAME;
+ 211: 	public static final String EXTENSIONS_TIMEOUT_THREAD_DUMP_ENABLED_PROPERTY_NAME = org.junit.jupiter.api.Constants.EXTENSIONS_TIMEOUT_THREAD_DUMP_ENABLED_PROPERTY_NAME;
  212: 
  213: 	/**
  214: 	 * Property name used to set the default test instance lifecycle mode: {@value}
  215: 	 *
  216: 	 * @see TestInstance.Lifecycle#DEFAULT_LIFECYCLE_PROPERTY_NAME
+ 217: 	 * @deprecated Please use
+ 218: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME}
+ 219: 	 * instead.
  220: 	 */
- : 	public static final String DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME = TestInstance.Lifecycle.DEFAULT_LIFECYCLE_PROPERTY_NAME;
+ 221: 	@API(status = DEPRECATED, since = "6.1")
+ 222: 	@Deprecated(forRemoval = true, since = "6.1")
+ 223: 	public static final String DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME;
  224: 
  225: 	/**
  226: 	 * Property name used to enable parallel test execution: {@value}
  227: 	 *
  228: 	 * <p>By default, tests are executed sequentially in a single thread.
  229: 	 *
  230: 	 * @since 5.3
+ 231: 	 * @deprecated Please use
+ 232: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME}
+ 233: 	 * instead.
  234: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME = JupiterConfiguration.PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME;
+ 235: 	@API(status = DEPRECATED, since = "6.1")
+ 236: 	@Deprecated(forRemoval = true, since = "6.1")
+ 237: 	public static final String PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME;
  238: 
  239: 	/**
  240: 	 * Property name used to enable auto-closing of {@link AutoCloseable} instances
  241: 	 *
  242: 	 * <p>By default, auto-closing is enabled.
  243: 	 *
  244: 	 * @since 5.13
+ 245: 	 * @deprecated Please use
+ 246: 	 * {@link org.junit.jupiter.api.Constants#CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME}
+ 247: 	 * instead.
  248: 	 */
- : 	@API(status = EXPERIMENTAL, since = "6.0")
- : 	public static final String CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME = JupiterConfiguration.CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME;
+ 249: 	@API(status = DEPRECATED, since = "6.1")
+ 250: 	@Deprecated(forRemoval = true, since = "6.1")
+ 251: 	public static final String CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME = org.junit.jupiter.api.Constants.CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME;
  252: 
  253: 	/**
  254: 	 * Property name used to set the default test execution mode: {@value}
  255: 	 *
  256: 	 * @see Execution#DEFAULT_EXECUTION_MODE_PROPERTY_NAME
+ 257: 	 * @deprecated Please use
+ 258: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_EXECUTION_MODE_PROPERTY_NAME}
+ 259: 	 * instead.
  260: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_PARALLEL_EXECUTION_MODE = Execution.DEFAULT_EXECUTION_MODE_PROPERTY_NAME;
+ 261: 	@API(status = DEPRECATED, since = "6.1")
+ 262: 	@Deprecated(forRemoval = true, since = "6.1")
+ 263: 	public static final String DEFAULT_PARALLEL_EXECUTION_MODE = org.junit.jupiter.api.Constants.DEFAULT_EXECUTION_MODE_PROPERTY_NAME;
  264: 
  265: 	/**
  266: 	 * Property name used to set the default test execution mode for top-level
  267: 	 * classes: {@value}
  268: 	 *
  269: 	 * @see Execution#DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME
+ 270: 	 * @deprecated Please use
+ 271: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME}
+ 272: 	 * instead.
  273: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME = Execution.DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME;
+ 274: 	@API(status = DEPRECATED, since = "6.1")
+ 275: 	@Deprecated(forRemoval = true, since = "6.1")
+ 276: 	public static final String DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME;
  277: 
  278: 	/**
- : 	 * Property name used to determine the desired
- : 	 * {@link ParallelExecutorServiceType ParallelExecutorServiceType}:
- : 	 * {@value}
+ 279: 	 * Property name used to determine the desired parallel executor service
+ 280: 	 * type: {@value}
  281: 	 *
- : 	 * <p>Value must be
- : 	 * {@link ParallelExecutorServiceType#FORK_JOIN_POOL FORK_JOIN_POOL} or
- : 	 * {@link ParallelExecutorServiceType#WORKER_THREAD_POOL WORKER_THREAD_POOL},
+ 282: 	 * <p>Value must be {@code FORK_JOIN_POOL} or {@code WORKER_THREAD_POOL},
  283: 	 * ignoring case.
  284: 	 *
  285: 	 * @since 6.1
- : 	 * @see ParallelHierarchicalTestExecutorServiceFactory
+ 286: 	 * @deprecated Please use
+ 287: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME}
+ 288: 	 * instead.
  289: 	 */
- : 	@API(status = EXPERIMENTAL, since = "6.1")
- : 	public static final String PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME;
+ 290: 	@API(status = DEPRECATED, since = "6.1")
+ 291: 	@Deprecated(forRemoval = true, since = "6.1")
+ 292: 	public static final String PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME;
  293: 
  294: 	/**
- : 	 * Property name used to select the
- : 	 * {@link ParallelExecutionConfigurationStrategy}: {@value}
+ 295: 	 * Property name used to select the parallel execution configuration
+ 296: 	 * strategy: {@value}
  297: 	 *
  298: 	 * <p>Potential values: {@code dynamic} (default), {@code fixed}, or
  299: 	 * {@code custom}.
  300: 	 *
  301: 	 * @since 5.3
+ 302: 	 * @deprecated Please use
+ 303: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_STRATEGY_PROPERTY_NAME}
+ 304: 	 * instead.
  305: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_CONFIG_STRATEGY_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_STRATEGY_PROPERTY_NAME;
+ 306: 	@API(status = DEPRECATED, since = "6.1")
+ 307: 	@Deprecated(forRemoval = true, since = "6.1")
+ 308: 	public static final String PARALLEL_CONFIG_STRATEGY_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_STRATEGY_PROPERTY_NAME;
  309: 
  310: 	/**
  311: 	 * Property name used to set the desired parallelism for the {@code fixed}
  312: 	 * configuration strategy: {@value}
  313: 	 *
  314: 	 * <p>No default value; must be a positive integer.
  315: 	 *
  316: 	 * @since 5.3
+ 317: 	 * @deprecated Please use
+ 318: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME}
+ 319: 	 * instead.
  320: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_FIXED_PARALLELISM_PROPERTY_NAME;
+ 321: 	@API(status = DEPRECATED, since = "6.1")
+ 322: 	@Deprecated(forRemoval = true, since = "6.1")
+ 323: 	public static final String PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME;
  324: 
  325: 	/**
  326: 	 * Property name used to configure the maximum pool size of the underlying
  327: 	 * fork-join pool for the {@code fixed} configuration strategy: {@value}
  328: 	 *
  329: 	 * <p>Value must be an integer and greater than or equal to
  330: 	 * {@value #PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME}; defaults to
  331: 	 * {@code 256 + fixed.parallelism}.
  332: 	 *
  333: 	 * @since 5.10
+ 334: 	 * @deprecated Please use
+ 335: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME}
+ 336: 	 * instead.
  337: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String PARALLEL_CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME;
+ 338: 	@API(status = DEPRECATED, since = "6.1")
+ 339: 	@Deprecated(forRemoval = true, since = "6.1")
+ 340: 	public static final String PARALLEL_CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME;
  341: 
  342: 	/**
  343: 	 * Property name used to disable saturation of the underlying fork-join pool
  344: 	 * for the {@code fixed} configuration strategy: {@value}
  345: 	 *
  346: 	 * <p>When set to {@code false} the underlying fork-join pool will reject
  347: 	 * additional tasks if all available workers are busy and the maximum
  348: 	 * pool-size would be exceeded.
  349: 	 *
  350: 	 * <p>Value must either {@code true} or {@code false}; defaults to {@code true}.
  351: 	 *
  352: 	 * @since 5.10
+ 353: 	 * @deprecated Please use
+ 354: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_FIXED_SATURATE_PROPERTY_NAME}
+ 355: 	 * instead.
  356: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String PARALLEL_CONFIG_FIXED_SATURATE_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_FIXED_SATURATE_PROPERTY_NAME;
+ 357: 	@API(status = DEPRECATED, since = "6.1")
+ 358: 	@Deprecated(forRemoval = true, since = "6.1")
+ 359: 	public static final String PARALLEL_CONFIG_FIXED_SATURATE_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_FIXED_SATURATE_PROPERTY_NAME;
  360: 
  361: 	/**
  362: 	 * Property name used to set the factor to be multiplied with the number of
  363: 	 * available processors/cores to determine the desired parallelism for the
  364: 	 * {@code dynamic} configuration strategy: {@value}
  365: 	 *
  366: 	 * <p>Value must be a positive decimal number; defaults to {@code 1}.
  367: 	 *
  368: 	 * @since 5.3
+ 369: 	 * @deprecated Please use
+ 370: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME}
+ 371: 	 * instead.
  372: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME;
+ 373: 	@API(status = DEPRECATED, since = "6.1")
+ 374: 	@Deprecated(forRemoval = true, since = "6.1")
+ 375: 	public static final String PARALLEL_CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME;
  376: 
  377: 	/**
  378: 	 * Property name used to specify the fully qualified class name of the
- : 	 * {@link ParallelExecutionConfigurationStrategy} to be used for the
- : 	 * {@code custom} configuration strategy: {@value}
+ 379: 	 * {@code custom} parallel execution configuration strategy to be used:
+ 380: 	 * {@value}
  381: 	 *
  382: 	 * @since 5.3
+ 383: 	 * @deprecated Please use
+ 384: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_CUSTOM_CLASS_PROPERTY_NAME}
+ 385: 	 * instead.
  386: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_CONFIG_CUSTOM_CLASS_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_CUSTOM_CLASS_PROPERTY_NAME;
+ 387: 	@API(status = DEPRECATED, since = "6.1")
+ 388: 	@Deprecated(forRemoval = true, since = "6.1")
+ 389: 	public static final String PARALLEL_CONFIG_CUSTOM_CLASS_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_CUSTOM_CLASS_PROPERTY_NAME;
  390: 
  391: 	/**
  392: 	 * Property name used to set the default timeout for all testable and
  393: 	 * lifecycle methods: {@value}.
  394: 	 *
  395: 	 * @see Timeout#DEFAULT_TIMEOUT_PROPERTY_NAME
+ 396: 	 * @deprecated Please use
+ 397: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TIMEOUT_PROPERTY_NAME}
+ 398: 	 * instead.
  399: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TIMEOUT_PROPERTY_NAME;
+ 400: 	@API(status = DEPRECATED, since = "6.1")
+ 401: 	@Deprecated(forRemoval = true, since = "6.1")
+ 402: 	public static final String DEFAULT_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TIMEOUT_PROPERTY_NAME;
  403: 
  404: 	/**
  405: 	 * Property name used to set the default timeout for all testable methods: {@value}.
  406: 	 *
  407: 	 * @see Timeout#DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME
+ 408: 	 * @deprecated Please use
+ 409: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME}
+ 410: 	 * instead.
  411: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 412: 	@API(status = DEPRECATED, since = "6.1")
+ 413: 	@Deprecated(forRemoval = true, since = "6.1")
+ 414: 	public static final String DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME;
  415: 
  416: 	/**
  417: 	 * Property name used to set the default timeout for all
  418: 	 * {@link Test @Test} methods: {@value}.
  419: 	 *
  420: 	 * @see Timeout#DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME
+ 421: 	 * @deprecated Please use
+ 422: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME}
+ 423: 	 * instead.
  424: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME;
+ 425: 	@API(status = DEPRECATED, since = "6.1")
+ 426: 	@Deprecated(forRemoval = true, since = "6.1")
+ 427: 	public static final String DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME;
  428: 
  429: 	/**
  430: 	 * Property name used to set the default timeout for all
  431: 	 * {@link TestTemplate @TestTemplate} methods: {@value}.
  432: 	 *
  433: 	 * @see Timeout#DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME
+ 434: 	 * @deprecated Please use
+ 435: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME}
+ 436: 	 * instead.
  437: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 438: 	@API(status = DEPRECATED, since = "6.1")
+ 439: 	@Deprecated(forRemoval = true, since = "6.1")
+ 440: 	public static final String DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME;
  441: 
  442: 	/**
  443: 	 * Property name used to set the default timeout for all
  444: 	 * {@link TestFactory @TestFactory} methods: {@value}.
  445: 	 *
  446: 	 * @see Timeout#DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME
+ 447: 	 * @deprecated Please use
+ 448: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME}
+ 449: 	 * instead.
  450: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME;
+ 451: 	@API(status = DEPRECATED, since = "6.1")
+ 452: 	@Deprecated(forRemoval = true, since = "6.1")
+ 453: 	public static final String DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME;
  454: 
  455: 	/**
  456: 	 * Property name used to set the default timeout for all lifecycle methods: {@value}.
  457: 	 *
  458: 	 * @see Timeout#DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME
+ 459: 	 * @deprecated Please use
+ 460: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME}
+ 461: 	 * instead.
  462: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 463: 	@API(status = DEPRECATED, since = "6.1")
+ 464: 	@Deprecated(forRemoval = true, since = "6.1")
+ 465: 	public static final String DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME;
  466: 
  467: 	/**
  468: 	 * Property name used to set the default timeout for all
  469: 	 * {@link BeforeAll @BeforeAll} methods: {@value}.
  470: 	 *
  471: 	 * @see Timeout#DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME
+ 472: 	 * @deprecated Please use
+ 473: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME}
+ 474: 	 * instead.
  475: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
+ 476: 	@API(status = DEPRECATED, since = "6.1")
+ 477: 	@Deprecated(forRemoval = true, since = "6.1")
+ 478: 	public static final String DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
  479: 
  480: 	/**
  481: 	 * Property name used to set the default timeout for all
  482: 	 * {@link BeforeEach @BeforeEach} methods: {@value}.
  483: 	 *
  484: 	 * @see Timeout#DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME
+ 485: 	 * @deprecated Please use
+ 486: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME}
+ 487: 	 * instead.
  488: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
+ 489: 	@API(status = DEPRECATED, since = "6.1")
+ 490: 	@Deprecated(forRemoval = true, since = "6.1")
+ 491: 	public static final String DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
  492: 
  493: 	/**
  494: 	 * Property name used to set the default timeout for all
  495: 	 * {@link AfterEach @AfterEach} methods: {@value}.
  496: 	 *
  497: 	 * @see Timeout#DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME
+ 498: 	 * @deprecated Please use
+ 499: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME}
+ 500: 	 * instead.
  501: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
+ 502: 	@API(status = DEPRECATED, since = "6.1")
+ 503: 	@Deprecated(forRemoval = true, since = "6.1")
+ 504: 	public static final String DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
  505: 
  506: 	/**
  507: 	 * Property name used to set the default timeout for all
  508: 	 * {@link AfterAll @AfterAll} methods: {@value}.
  509: 	 *
  510: 	 * @see Timeout#DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME
+ 511: 	 * @deprecated Please use
+ 512: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME}
+ 513: 	 * instead.
  514: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
+ 515: 	@API(status = DEPRECATED, since = "6.1")
+ 516: 	@Deprecated(forRemoval = true, since = "6.1")
+ 517: 	public static final String DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
  518: 
  519: 	/**
  520: 	 * Property name used to configure whether timeouts are applied to tests: {@value}.
  521: 	 *
  522: 	 * @see Timeout#TIMEOUT_MODE_PROPERTY_NAME
+ 523: 	 * @deprecated Please use
+ 524: 	 * {@link org.junit.jupiter.api.Constants#TIMEOUT_MODE_PROPERTY_NAME}
+ 525: 	 * instead.
  526: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String TIMEOUT_MODE_PROPERTY_NAME = Timeout.TIMEOUT_MODE_PROPERTY_NAME;
+ 527: 	@API(status = DEPRECATED, since = "6.1")
+ 528: 	@Deprecated(forRemoval = true, since = "6.1")
+ 529: 	public static final String TIMEOUT_MODE_PROPERTY_NAME = org.junit.jupiter.api.Constants.TIMEOUT_MODE_PROPERTY_NAME;
  530: 
  531: 	/**
  532: 	 * Property name used to set the default method orderer class name: {@value}
  533: 	 *
  534: 	 * @see MethodOrderer#DEFAULT_ORDER_PROPERTY_NAME
+ 535: 	 * @deprecated Please use
+ 536: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME}
+ 537: 	 * instead.
  538: 	 */
- : 	@API(status = STABLE, since = "5.9")
- : 	public static final String DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME = MethodOrderer.DEFAULT_ORDER_PROPERTY_NAME;
+ 539: 	@API(status = DEPRECATED, since = "6.1")
+ 540: 	@Deprecated(forRemoval = true, since = "6.1")
+ 541: 	public static final String DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME;
  542: 
  543: 	/**
  544: 	 * Property name used to set the default class orderer class name: {@value}
  545: 	 *
  546: 	 * @see ClassOrderer#DEFAULT_ORDER_PROPERTY_NAME
+ 547: 	 * @deprecated Please use
+ 548: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_CLASS_ORDER_PROPERTY_NAME}
+ 549: 	 * instead.
  550: 	 */
- : 	@API(status = STABLE, since = "5.9")
- : 	public static final String DEFAULT_TEST_CLASS_ORDER_PROPERTY_NAME = ClassOrderer.DEFAULT_ORDER_PROPERTY_NAME;
+ 551: 	@API(status = DEPRECATED, since = "6.1")
+ 552: 	@Deprecated(forRemoval = true, since = "6.1")
+ 553: 	public static final String DEFAULT_TEST_CLASS_ORDER_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_CLASS_ORDER_PROPERTY_NAME;
  554: 
  555: 	/**
  556: 	 * Property name used to set the default timeout thread mode.
  557: 	 *
  558: 	 * @since 5.9
  559: 	 * @see Timeout
  560: 	 * @see Timeout.ThreadMode
+ 561: 	 * @deprecated Please use
+ 562: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME}
+ 563: 	 * instead.
  564: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME = Timeout.DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME;
+ 565: 	@API(status = DEPRECATED, since = "6.1")
+ 566: 	@Deprecated(forRemoval = true, since = "6.1")
+ 567: 	public static final String DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME;
  568: 
  569: 	/**
  570: 	 * Property name used to set the default factory for temporary directories created via
  571: 	 * the {@link TempDir @TempDir} annotation: {@value}
  572: 	 *
  573: 	 * @since 5.10
  574: 	 * @see TempDir#DEFAULT_FACTORY_PROPERTY_NAME
+ 575: 	 * @deprecated Please use
+ 576: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEMP_DIR_FACTORY_PROPERTY_NAME}
+ 577: 	 * instead.
  578: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String DEFAULT_TEMP_DIR_FACTORY_PROPERTY_NAME = TempDir.DEFAULT_FACTORY_PROPERTY_NAME;
+ 579: 	@API(status = DEPRECATED, since = "6.1")
+ 580: 	@Deprecated(forRemoval = true, since = "6.1")
+ 581: 	public static final String DEFAULT_TEMP_DIR_FACTORY_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEMP_DIR_FACTORY_PROPERTY_NAME;
  582: 
  583: 	/**
  584: 	 * Property name used to set the default extension context scope for
  585: 	 * extensions that participate in test instantiation: {@value}
  586: 	 *
  587: 	 * @since 5.12
  588: 	 * @see org.junit.jupiter.api.extension.TestInstantiationAwareExtension
+ 589: 	 * @deprecated Please use
+ 590: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_CLASS_INSTANCE_CONSTRUCTION_EXTENSION_CONTEXT_SCOPE_PROPERTY_NAME}
+ 591: 	 * instead.
  592: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String DEFAULT_TEST_CLASS_INSTANCE_CONSTRUCTION_EXTENSION_CONTEXT_SCOPE_PROPERTY_NAME = ExtensionContextScope.DEFAULT_SCOPE_PROPERTY_NAME;
+ 593: 	@API(status = DEPRECATED, since = "6.1")
+ 594: 	@Deprecated(forRemoval = true, since = "6.1")
+ 595: 	public static final String DEFAULT_TEST_CLASS_INSTANCE_CONSTRUCTION_EXTENSION_CONTEXT_SCOPE_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_CLASS_INSTANCE_CONSTRUCTION_EXTENSION_CONTEXT_SCOPE_PROPERTY_NAME;
  596: 
  597: 	private Constants() {
  598: 		/* no-op */
  599: 	}
  600: 
  601: }
```

**The reviewer's comment:**

> The deprecated field now delegates to org.junit.jupiter.api.Constants instead of being a direct alias. This could break compatibility if the target constant has different behavior.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 42. `qwen__qwen3-coder-30b-a3b-instruct__mockito__mockito__2807__unmatched_model__21`

**Arm:** `qwen`  •  **File:** `src/main/java/org/mockito/internal/matchers/Null.java`  •  **comment on line 26**  •  [PR #2807](https://github.com/mockito/mockito/pull/2807)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  1: /*
  2:  * Copyright (c) 2007 Mockito contributors
  3:  * This program is made available under the terms of the MIT License.
  4:  */
  5: package org.mockito.internal.matchers;
  6: 
  7: import java.io.Serializable;
  8: 
  9: import org.mockito.ArgumentMatcher;
  10: 
- : public class Null implements ArgumentMatcher<Object>, Serializable {
+ 11: public class Null<T> implements ArgumentMatcher<T>, Serializable {
  12: 
- :     public static final Null NULL = new Null();
+ 13:     public static final Null<Object> NULL = new Null<>(Object.class);
+ 14:     private final Class<T> type;
  15: 
- :     private Null() {}
+ 16:     public Null(Class<T> type) {
+ 17:         this.type = type;
+ 18:     }
  19: 
  20:     @Override
  21:     public boolean matches(Object actual) {
  22:         return actual == null;
  23:     }
  24: 
+ 25:     @Override
+ 26:     public Class<T> type() {
+ 27:         return type;
+ 28:     }
+ 29: 
  30:     @Override
  31:     public String toString() {
  32:         return "isNull()";
  33:     }
  34: }
```

**The reviewer's comment:**

> Adding a new 'type()' method to the ArgumentMatcher interface may require updates to other implementations or usage patterns.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 43. `qwen__qwen3-coder-30b-a3b-instruct__checkstyle__checkstyle__21086__unmatched_model__22`

**Arm:** `qwen`  •  **File:** `src/main/resources/com/puppycrawl/tools/checkstyle/meta/checks/javadoc/WriteTagCheck.xml`  •  **comment on line 41**  •  [PR #21086](https://github.com/checkstyle/checkstyle/pull/21086)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  28:             <property default-value="INTERFACE_DEF,CLASS_DEF,ENUM_DEF,ANNOTATION_DEF,RECORD_DEF"
  29:                       name="tokens"
  30:                       type="java.lang.String[]"
  31:                       validation-type="tokenSet">
  32:                <description>tokens to check</description>
  33:             </property>
  34:             <property default-value="false"
  35:                       name="violateExecutionOnNonTightHtml"
  36:                       type="boolean">
  37:                <description>Control when to print violations if the Javadoc being examined by this check violates the tight html rules defined at &lt;a href="https://checkstyle.org/writingjavadocchecks.html#Tight-HTML_rules"&gt;Tight-HTML Rules&lt;/a&gt;.</description>
  38:             </property>
  39:          </properties>
  40:          <message-keys>
+ 41:             <message-key key="javadoc.missingTag"/>
  42:             <message-key key="javadoc.parse.rule.error"/>
+ 43:             <message-key key="javadoc.tagFormat"/>
  44:             <message-key key="javadoc.unclosedHtml"/>
  45:             <message-key key="javadoc.writeTag"/>
- :             <message-key key="type.missingTag"/>
- :             <message-key key="type.tagFormat"/>
  46:          </message-keys>
  47:       </check>
  48:    </module>
  49: </checkstyle-metadata>
```

**The reviewer's comment:**

> Added message key 'javadoc.missingTag' which may indicate a change in validation logic or error reporting scope. Verify that this change aligns with the intended behavior of WriteTagCheck.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 44. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5424__unmatched_model__58`

**Arm:** `qwen`  •  **File:** `jupiter-tests/src/test/java/org/junit/jupiter/engine/extension/TempDirectoryTests.java`  •  **comment on line 1295**  •  [PR #5424](https://github.com/junit-team/junit5/pull/5424)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  1247: 			assertAllTempDirsExist(testInfo);
  1248: 		}
  1249: 
  1250: 		@AfterAll
  1251: 		static void afterAll(@TempDir Path param1, @TempDir Path param2, TestInfo testInfo) {
  1252: 			getTempDirs(testInfo).putAll(Map.of( //
  1253: 				"afterAll1", param1, //
  1254: 				"afterAll2", param2 //
  1255: 			));
  1256: 			assertAllTempDirsExist(testInfo);
  1257: 		}
  1258: 
  1259: 		private static Map<String, Path> getTempDirs(TestInfo testInfo) {
- : 			return tempDirs.computeIfAbsent(testInfo.getDisplayName(), __ -> new LinkedHashMap<>());
+ 1260: 			return tempDirs.computeIfAbsent(testInfo.getDisplayName(), _ -> new LinkedHashMap<>());
  1261: 		}
  1262: 
  1263: 		private static void assertAllTempDirsExist(TestInfo testInfo) {
  1264: 			assertAll(getTempDirs(testInfo).values().stream().map(tempDir -> () -> assertTrue(Files.exists(tempDir))));
  1265: 		}
  1266: 	}
  1267: 
  1268: 	static class UndeletableTestCase {
  1269: 
- : 		static final Path UNDELETABLE_PATH = Path.of("undeletable");
  1270: 		static final String TEMP_DIR = "TEMP_DIR";
  1271: 
- : 		@RegisterExtension
- : 		BeforeEachCallback injector = context -> context //
- : 				.getStore(TempDirectory.NAMESPACE) //
- : 				.put(TempDirectory.FILE_OPERATIONS_KEY, (FileOperations) path -> {
- : 					if (path.endsWith(UNDELETABLE_PATH)) {
- : 						throw new IOException("Simulated failure");
- : 					}
- : 					else {
- : 						Files.delete(path);
- : 					}
- : 				});
- : 
- : 		@TempDir
+ 1272: 		@TempDir(deletionStrategy = FailingTempDirDeletionStrategy.class)
  1273: 		Path tempDir;
  1274: 
  1275: 		@BeforeEach
  1276: 		void reportTempDir(TestReporter reporter) {
  1277: 			reporter.publishEntry(TEMP_DIR, tempDir.toString());
  1278: 		}
  1279: 	}
  1280: 
  1281: 	static class UndeletableDirectoryTestCase extends UndeletableTestCase {
  1282: 		@Test
  1283: 		void test() throws Exception {
  1284: 			Files.createDirectory(tempDir.resolve(UNDELETABLE_PATH));
  1285: 		}
  1286: 	}
  1287: 
  1288: 	static class UndeletableFileTestCase extends UndeletableTestCase {
  1289: 		@Test
  1290: 		void test() throws Exception {
  1291: 			Files.createFile(tempDir.resolve(UNDELETABLE_PATH));
  1292: 		}
  1293: 	}
  1294: 
+ 1295: 	static class UndeletableWithDefaultDeletionStrategyTestCase extends UndeletableTestCase {
+ 1296: 
+ 1297: 		static final String TEMP_DIR = "TEMP_DIR";
+ 1298: 
+ 1299: 		@TempDir
+ 1300: 		Path tempDir;
+ 1301: 
+ 1302: 		@BeforeEach
+ 1303: 		void reportTempDir(TestReporter reporter) {
+ 1304: 			reporter.publishEntry(TEMP_DIR, tempDir.toString());
+ 1305: 		}
+ 1306: 
+ 1307: 		@Test
+ 1308: 		void test() throws Exception {
+ 1309: 			Files.createFile(tempDir.resolve(UNDELETABLE_PATH));
+ 1310: 		}
+ 1311: 	}
+ 1312: 
  1313: 	static class FactoryWithTestMethodNameAsPrefixTestCase {
  1314: 
  1315: 		@Test
  1316: 		void test(@TempDir(factory = Factory.class) Path tempDir) {
  1317: 			assertTrue(Files.exists(tempDir));
  1318: 			assertThat(tempDir.getFileName()).asString().startsWith("test");
  1319: 		}
  1320: 
  1321: 		@NullMarked
  1322: 		private static class Factory implements TempDirFactory {
  1323: 
  1324: 			@Override
  1325: 			public Path createTempDirectory(AnnotatedElementContext elementContext, ExtensionContext extensionContext)
```

**The reviewer's comment:**

> Adding a new test case with default deletion strategy might conflict with existing behavior. Verify that this doesn't introduce unexpected side effects.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 45. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5424__unmatched_model__42`

**Arm:** `qwen`  •  **File:** `jupiter-tests/src/test/java/org/junit/jupiter/engine/extension/CloseablePathTests.java`  •  **comment on line 222**  •  [PR #5424](https://github.com/junit-team/junit5/pull/5424)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  121: 		void setUpRootFolder() throws IOException {
  122: 			root = createTempDirectory("root");
  123: 		}
  124: 
  125: 		@AfterEach
  126: 		void cleanupRoot() throws IOException {
  127: 			delete(root);
  128: 		}
  129: 
  130: 		@DisplayName("succeeds if the factory returns a directory")
  131: 		@ParameterizedTest
  132: 		@ElementTypeSource
  133: 		void factoryReturnsDirectoryDynamic(Class<?> elementType) throws IOException {
- : 			TempDirFactory factory = (elementContext, extensionContext) -> createDirectory(root.resolve("directory"));
+ 134: 			TempDirFactory factory = (_, _) -> createDirectory(root.resolve("directory"));
  135: 
- : 			closeablePath = TempDirectory.createTempDir(factory, DEFAULT, elementType, elementContext,
+ 136: 			closeablePath = TempDirectory.createTempDir(factory, cleanup(ALWAYS), elementType, elementContext,
  137: 				extensionContext);
  138: 			assertThat(closeablePath.get()).isDirectory();
  139: 
  140: 			delete(closeablePath.get());
  141: 		}
  142: 
  143: 		@DisplayName("succeeds if the factory returns a symbolic link to a directory")
  144: 		@ParameterizedTest
  145: 		@ElementTypeSource
  146: 		@DisabledOnOs(WINDOWS)
  147: 		void factoryReturnsSymbolicLinkToDirectory(Class<?> elementType) throws IOException {
  148: 			Path directory = createDirectory(root.resolve("directory"));
- : 			TempDirFactory factory = (elementContext,
- : 					extensionContext) -> createSymbolicLink(root.resolve("symbolicLink"), directory);
+ 149: 			TempDirFactory factory = (_, _) -> createSymbolicLink(root.resolve("symbolicLink"), directory);
  150: 
- : 			closeablePath = TempDirectory.createTempDir(factory, DEFAULT, elementType, elementContext,
+ 151: 			closeablePath = TempDirectory.createTempDir(factory, cleanup(ALWAYS), elementType, elementContext,
  152: 				extensionContext);
  153: 			assertThat(closeablePath.get()).isDirectory();
  154: 
  155: 			delete(closeablePath.get());
  156: 			delete(directory);
  157: 		}
  158: 
  159: 		@DisplayName("succeeds if the factory returns a directory on a non-default file system for a Path annotated element")
  160: 		@Test
  161: 		void factoryReturnsDirectoryOnNonDefaultFileSystemWithPath() throws IOException {
  162: 			TempDirFactory factory = new JimfsFactory();
  163: 
- : 			closeablePath = TempDirectory.createTempDir(factory, DEFAULT, Path.class, elementContext, extensionContext);
+ 164: 			closeablePath = TempDirectory.createTempDir(factory, cleanup(ALWAYS), Path.class, elementContext,
+ 165: 				extensionContext);
  166: 			assertThat(closeablePath.get()).isDirectory();
  167: 
  168: 			delete(closeablePath.get());
  169: 		}
  170: 
  171: 		@SuppressWarnings("DataFlowIssue")
  172: 		@DisplayName("fails if the factory returns null")
  173: 		@ParameterizedTest
  174: 		@ElementTypeSource
  175: 		void factoryReturnsNull(Class<?> elementType) throws IOException {
  176: 			TempDirFactory factory = spy(new Factory(null));
  177: 
- : 			assertThatExtensionConfigurationExceptionIsThrownBy(
- : 				() -> TempDirectory.createTempDir(factory, DEFAULT, elementType, elementContext, extensionContext));
+ 178: 			assertThatExtensionConfigurationExceptionIsThrownBy(() -> TempDirectory.createTempDir(factory,
+ 179: 				cleanup(ALWAYS), elementType, elementContext, extensionContext));
  180: 
  181: 			verify(factory).close();
  182: 		}
  183: 
  184: 		@DisplayName("fails if the factory returns a file")
  185: 		@ParameterizedTest
  186: 		@ElementTypeSource
  187: 		void factoryReturnsFile(Class<?> elementType) throws IOException {
  188: 			Path file = createFile(root.resolve("file"));
  189: 			TempDirFactory factory = spy(new Factory(file));
  190: 
- : 			assertThatExtensionConfigurationExceptionIsThrownBy(
- : 				() -> TempDirectory.createTempDir(factory, DEFAULT, elementType, elementContext, extensionContext));
+ 191: 			assertThatExtensionConfigurationExceptionIsThrownBy(() -> TempDirectory.createTempDir(factory,
+ 192: 				cleanup(ALWAYS), elementType, elementContext, extensionContext));
  193: 
  194: 			verify(factory).close();
  195: 			assertThat(file).doesNotExist();
  196: 		}
  197: 
  198: 		@DisplayName("fails if the factory returns a symbolic link to a file")
  199: 		@ParameterizedTest
  200: 		@ElementTypeSource
  201: 		@DisabledOnOs(WINDOWS)
  202: 		void factoryReturnsSymbolicLinkToFile(Class<?> elementType) throws IOException {
  203: 			Path file = createFile(root.resolve("file"));
  204: 			Path symbolicLink = createSymbolicLink(root.resolve("symbolicLink"), file);
  205: 			TempDirFactory factory = spy(new Factory(symbolicLink));
  206: 
- : 			assertThatExtensionConfigurationExceptionIsThrownBy(
- : 				() -> TempDirectory.createTempDir(factory, DEFAULT, elementType, elementContext, extensionContext));
+ 207: 			assertThatExtensionConfigurationExceptionIsThrownBy(() -> TempDirectory.createTempDir(factory,
+ 208: 				cleanup(ALWAYS), elementType, elementContext, extensionContext));
  209: 
  210: 			verify(factory).close();
  211: 			assertThat(symbolicLink).doesNotExist();
  212: 
  213: 			delete(file);
  214: 		}
  215: 
  216: 		@DisplayName("fails if the factory returns a directory on a non-default file system for a File annotated element")
  217: 		@Test
  218: 		void factoryReturnsDirectoryOnNonDefaultFileSystemWithFile() throws IOException {
  219: 			TempDirFactory factory = spy(new JimfsFactory());
  220: 
  221: 			assertThatExceptionOfType(ExtensionConfigurationException.class)//
- : 					.isThrownBy(() -> TempDirectory.createTempDir(factory, DEFAULT, File.class, elementContext,
+ 222: 					.isThrownBy(() -> TempDirectory.createTempDir(factory, cleanup(ALWAYS), File.class, elementContext,
  223: 						extensionContext))//
  224: 					.withMessage("Failed to create default temp directory")//
  225: 					.withCauseInstanceOf(PreconditionViolationException.class)//
  226: 					.havingCause().withMessage("temp directory with non-default file system cannot be injected into "
  227: 							+ File.class.getName() + " target");
  228: 
  229: 			verify(factory).close();
  230: 		}
  231: 
  232: 		// Mockito spying a lambda fails with: VM does not support modification of given type
+ 233: 		@NullMarked
  234: 		private record Factory(Path path) implements TempDirFactory {
  235: 
  236: 			@Override
  237: 			public Path createTempDirectory(AnnotatedElementContext elementContext, ExtensionContext extensionContext) {
  238: 				return path;
  239: 			}
  240: 
  241: 		}
  242: 
+ 243: 		@NullMarked
  244: 		private static class JimfsFactory implements TempDirFactory {
  245: 
  246: 			private final FileSystem fileSystem = Jimfs.newFileSystem(unix());
  247: 
  248: 			@Override
  249: 			public Path createTempDirectory(AnnotatedElementContext elementContext, ExtensionContext extensionContext)
  250: 					throws Exception {
  251: 				return createDirectory(fileSystem.getPath("/").resolve("directory"));
  252: 			}
  253: 
  254: 			@Override
  255: 			public void close() throws IOException {
  256: 				fileSystem.close();
```

**The reviewer's comment:**

> Adding cleanup(ALWAYS) parameter improves test reliability by ensuring cleanup happens regardless of test outcome.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---

## 46. `qwen__qwen3-coder-30b-a3b-instruct__junit-team__junit5__5379__unmatched_model__28`

**Arm:** `qwen`  •  **File:** `junit-jupiter-engine/src/main/java/org/junit/jupiter/engine/Constants.java`  •  **comment on line 463**  •  [PR #5379](https://github.com/junit-team/junit5/pull/5379)

**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):

```diff
  143: 	 * <li>{@code *.MyCondition}: deactivates every condition whose simple class name is
  144: 	 * exactly {@code MyCondition}.
  145: 	 * <li>{@code *System*}: deactivates every condition whose FQCN contains
  146: 	 * {@code System}.
  147: 	 * <li>{@code *System*, *Dev*}: deactivates every condition whose FQCN contains
  148: 	 * {@code System} or {@code Dev}.
  149: 	 * <li>{@code org.example.MyCondition, org.example.TheirCondition}: deactivates
  150: 	 * conditions whose FQCN is exactly {@code org.example.MyCondition} or
  151: 	 * {@code org.example.TheirCondition}.
  152: 	 * </ul>
  153: 	 *
  154: 	 * @see #DEACTIVATE_ALL_CONDITIONS_PATTERN
  155: 	 * @see org.junit.jupiter.api.extension.ExecutionCondition
+ 156: 	 * @deprecated Please use
+ 157: 	 * {@link org.junit.jupiter.api.Constants#DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME}
+ 158: 	 * instead.
  159: 	 */
- : 	public static final String DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME = JupiterConfiguration.DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME;
+ 160: 	@API(status = DEPRECATED, since = "6.1")
+ 161: 	@Deprecated(forRemoval = true, since = "6.1")
+ 162: 	public static final String DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME;
  163: 
  164: 	/**
  165: 	 * Wildcard pattern which signals that all conditions should be deactivated: {@value}
  166: 	 *
  167: 	 * @see #DEACTIVATE_CONDITIONS_PATTERN_PROPERTY_NAME
  168: 	 * @see org.junit.jupiter.api.extension.ExecutionCondition
+ 169: 	 * @deprecated Please use
+ 170: 	 * {@link org.junit.jupiter.api.Constants#DEACTIVATE_ALL_CONDITIONS_PATTERN}
+ 171: 	 * instead.
  172: 	 */
- : 	public static final String DEACTIVATE_ALL_CONDITIONS_PATTERN = ClassNamePatternFilterUtils.ALL_PATTERN;
+ 173: 	@API(status = DEPRECATED, since = "6.1")
+ 174: 	@Deprecated(forRemoval = true, since = "6.1")
+ 175: 	public static final String DEACTIVATE_ALL_CONDITIONS_PATTERN = org.junit.jupiter.api.Constants.DEACTIVATE_ALL_CONDITIONS_PATTERN;
  176: 
  177: 	/**
  178: 	 * Property name used to set the default display name generator class name: {@value}
  179: 	 *
  180: 	 * @see DisplayNameGenerator#DEFAULT_GENERATOR_PROPERTY_NAME
+ 181: 	 * @deprecated Please use
+ 182: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME}
+ 183: 	 * instead.
  184: 	 */
- : 	public static final String DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME = DisplayNameGenerator.DEFAULT_GENERATOR_PROPERTY_NAME;
+ 185: 	@API(status = DEPRECATED, since = "6.1")
+ 186: 	@Deprecated(forRemoval = true, since = "6.1")
+ 187: 	public static final String DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_DISPLAY_NAME_GENERATOR_PROPERTY_NAME;
  188: 
  189: 	/**
  190: 	 * Property name used to enable auto-detection and registration of extensions via
  191: 	 * Java's {@link java.util.ServiceLoader} mechanism: {@value}
  192: 	 *
  193: 	 * <p>The default behavior is not to perform auto-detection.
+ 194: 	 * @deprecated Please use
+ 195: 	 * {@link org.junit.jupiter.api.Constants#EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME}
+ 196: 	 * instead.
  197: 	 */
- : 	public static final String EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME = JupiterConfiguration.EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME;
+ 198: 	@API(status = DEPRECATED, since = "6.1")
+ 199: 	@Deprecated(forRemoval = true, since = "6.1")
+ 200: 	public static final String EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME = org.junit.jupiter.api.Constants.EXTENSIONS_AUTODETECTION_ENABLED_PROPERTY_NAME;
  201: 
  202: 	/**
  203: 	 * Property name used to enable dumping the stack of all
  204: 	 * {@linkplain Thread threads} to {@code System.out} when a timeout has occurred.
  205: 	 *
  206: 	 * <p>This behavior is disabled by default.
  207: 	 *
  208: 	 * @since 5.12
  209: 	 */
  210: 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String EXTENSIONS_TIMEOUT_THREAD_DUMP_ENABLED_PROPERTY_NAME = JupiterConfiguration.EXTENSIONS_TIMEOUT_THREAD_DUMP_ENABLED_PROPERTY_NAME;
+ 211: 	public static final String EXTENSIONS_TIMEOUT_THREAD_DUMP_ENABLED_PROPERTY_NAME = org.junit.jupiter.api.Constants.EXTENSIONS_TIMEOUT_THREAD_DUMP_ENABLED_PROPERTY_NAME;
  212: 
  213: 	/**
  214: 	 * Property name used to set the default test instance lifecycle mode: {@value}
  215: 	 *
  216: 	 * @see TestInstance.Lifecycle#DEFAULT_LIFECYCLE_PROPERTY_NAME
+ 217: 	 * @deprecated Please use
+ 218: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME}
+ 219: 	 * instead.
  220: 	 */
- : 	public static final String DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME = TestInstance.Lifecycle.DEFAULT_LIFECYCLE_PROPERTY_NAME;
+ 221: 	@API(status = DEPRECATED, since = "6.1")
+ 222: 	@Deprecated(forRemoval = true, since = "6.1")
+ 223: 	public static final String DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_INSTANCE_LIFECYCLE_PROPERTY_NAME;
  224: 
  225: 	/**
  226: 	 * Property name used to enable parallel test execution: {@value}
  227: 	 *
  228: 	 * <p>By default, tests are executed sequentially in a single thread.
  229: 	 *
  230: 	 * @since 5.3
+ 231: 	 * @deprecated Please use
+ 232: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME}
+ 233: 	 * instead.
  234: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME = JupiterConfiguration.PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME;
+ 235: 	@API(status = DEPRECATED, since = "6.1")
+ 236: 	@Deprecated(forRemoval = true, since = "6.1")
+ 237: 	public static final String PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_EXECUTION_ENABLED_PROPERTY_NAME;
  238: 
  239: 	/**
  240: 	 * Property name used to enable auto-closing of {@link AutoCloseable} instances
  241: 	 *
  242: 	 * <p>By default, auto-closing is enabled.
  243: 	 *
  244: 	 * @since 5.13
+ 245: 	 * @deprecated Please use
+ 246: 	 * {@link org.junit.jupiter.api.Constants#CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME}
+ 247: 	 * instead.
  248: 	 */
- : 	@API(status = EXPERIMENTAL, since = "6.0")
- : 	public static final String CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME = JupiterConfiguration.CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME;
+ 249: 	@API(status = DEPRECATED, since = "6.1")
+ 250: 	@Deprecated(forRemoval = true, since = "6.1")
+ 251: 	public static final String CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME = org.junit.jupiter.api.Constants.CLOSING_STORED_AUTO_CLOSEABLE_ENABLED_PROPERTY_NAME;
  252: 
  253: 	/**
  254: 	 * Property name used to set the default test execution mode: {@value}
  255: 	 *
  256: 	 * @see Execution#DEFAULT_EXECUTION_MODE_PROPERTY_NAME
+ 257: 	 * @deprecated Please use
+ 258: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_EXECUTION_MODE_PROPERTY_NAME}
+ 259: 	 * instead.
  260: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_PARALLEL_EXECUTION_MODE = Execution.DEFAULT_EXECUTION_MODE_PROPERTY_NAME;
+ 261: 	@API(status = DEPRECATED, since = "6.1")
+ 262: 	@Deprecated(forRemoval = true, since = "6.1")
+ 263: 	public static final String DEFAULT_PARALLEL_EXECUTION_MODE = org.junit.jupiter.api.Constants.DEFAULT_EXECUTION_MODE_PROPERTY_NAME;
  264: 
  265: 	/**
  266: 	 * Property name used to set the default test execution mode for top-level
  267: 	 * classes: {@value}
  268: 	 *
  269: 	 * @see Execution#DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME
+ 270: 	 * @deprecated Please use
+ 271: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME}
+ 272: 	 * instead.
  273: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME = Execution.DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME;
+ 274: 	@API(status = DEPRECATED, since = "6.1")
+ 275: 	@Deprecated(forRemoval = true, since = "6.1")
+ 276: 	public static final String DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_CLASSES_EXECUTION_MODE_PROPERTY_NAME;
  277: 
  278: 	/**
- : 	 * Property name used to determine the desired
- : 	 * {@link ParallelExecutorServiceType ParallelExecutorServiceType}:
- : 	 * {@value}
+ 279: 	 * Property name used to determine the desired parallel executor service
+ 280: 	 * type: {@value}
  281: 	 *
- : 	 * <p>Value must be
- : 	 * {@link ParallelExecutorServiceType#FORK_JOIN_POOL FORK_JOIN_POOL} or
- : 	 * {@link ParallelExecutorServiceType#WORKER_THREAD_POOL WORKER_THREAD_POOL},
+ 282: 	 * <p>Value must be {@code FORK_JOIN_POOL} or {@code WORKER_THREAD_POOL},
  283: 	 * ignoring case.
  284: 	 *
  285: 	 * @since 6.1
- : 	 * @see ParallelHierarchicalTestExecutorServiceFactory
+ 286: 	 * @deprecated Please use
+ 287: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME}
+ 288: 	 * instead.
  289: 	 */
- : 	@API(status = EXPERIMENTAL, since = "6.1")
- : 	public static final String PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME;
+ 290: 	@API(status = DEPRECATED, since = "6.1")
+ 291: 	@Deprecated(forRemoval = true, since = "6.1")
+ 292: 	public static final String PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_EXECUTOR_SERVICE_PROPERTY_NAME;
  293: 
  294: 	/**
- : 	 * Property name used to select the
- : 	 * {@link ParallelExecutionConfigurationStrategy}: {@value}
+ 295: 	 * Property name used to select the parallel execution configuration
+ 296: 	 * strategy: {@value}
  297: 	 *
  298: 	 * <p>Potential values: {@code dynamic} (default), {@code fixed}, or
  299: 	 * {@code custom}.
  300: 	 *
  301: 	 * @since 5.3
+ 302: 	 * @deprecated Please use
+ 303: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_STRATEGY_PROPERTY_NAME}
+ 304: 	 * instead.
  305: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_CONFIG_STRATEGY_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_STRATEGY_PROPERTY_NAME;
+ 306: 	@API(status = DEPRECATED, since = "6.1")
+ 307: 	@Deprecated(forRemoval = true, since = "6.1")
+ 308: 	public static final String PARALLEL_CONFIG_STRATEGY_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_STRATEGY_PROPERTY_NAME;
  309: 
  310: 	/**
  311: 	 * Property name used to set the desired parallelism for the {@code fixed}
  312: 	 * configuration strategy: {@value}
  313: 	 *
  314: 	 * <p>No default value; must be a positive integer.
  315: 	 *
  316: 	 * @since 5.3
+ 317: 	 * @deprecated Please use
+ 318: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME}
+ 319: 	 * instead.
  320: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_FIXED_PARALLELISM_PROPERTY_NAME;
+ 321: 	@API(status = DEPRECATED, since = "6.1")
+ 322: 	@Deprecated(forRemoval = true, since = "6.1")
+ 323: 	public static final String PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME;
  324: 
  325: 	/**
  326: 	 * Property name used to configure the maximum pool size of the underlying
  327: 	 * fork-join pool for the {@code fixed} configuration strategy: {@value}
  328: 	 *
  329: 	 * <p>Value must be an integer and greater than or equal to
  330: 	 * {@value #PARALLEL_CONFIG_FIXED_PARALLELISM_PROPERTY_NAME}; defaults to
  331: 	 * {@code 256 + fixed.parallelism}.
  332: 	 *
  333: 	 * @since 5.10
+ 334: 	 * @deprecated Please use
+ 335: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME}
+ 336: 	 * instead.
  337: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String PARALLEL_CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME;
+ 338: 	@API(status = DEPRECATED, since = "6.1")
+ 339: 	@Deprecated(forRemoval = true, since = "6.1")
+ 340: 	public static final String PARALLEL_CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_FIXED_MAX_POOL_SIZE_PROPERTY_NAME;
  341: 
  342: 	/**
  343: 	 * Property name used to disable saturation of the underlying fork-join pool
  344: 	 * for the {@code fixed} configuration strategy: {@value}
  345: 	 *
  346: 	 * <p>When set to {@code false} the underlying fork-join pool will reject
  347: 	 * additional tasks if all available workers are busy and the maximum
  348: 	 * pool-size would be exceeded.
  349: 	 *
  350: 	 * <p>Value must either {@code true} or {@code false}; defaults to {@code true}.
  351: 	 *
  352: 	 * @since 5.10
+ 353: 	 * @deprecated Please use
+ 354: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_FIXED_SATURATE_PROPERTY_NAME}
+ 355: 	 * instead.
  356: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String PARALLEL_CONFIG_FIXED_SATURATE_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_FIXED_SATURATE_PROPERTY_NAME;
+ 357: 	@API(status = DEPRECATED, since = "6.1")
+ 358: 	@Deprecated(forRemoval = true, since = "6.1")
+ 359: 	public static final String PARALLEL_CONFIG_FIXED_SATURATE_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_FIXED_SATURATE_PROPERTY_NAME;
  360: 
  361: 	/**
  362: 	 * Property name used to set the factor to be multiplied with the number of
  363: 	 * available processors/cores to determine the desired parallelism for the
  364: 	 * {@code dynamic} configuration strategy: {@value}
  365: 	 *
  366: 	 * <p>Value must be a positive decimal number; defaults to {@code 1}.
  367: 	 *
  368: 	 * @since 5.3
+ 369: 	 * @deprecated Please use
+ 370: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME}
+ 371: 	 * instead.
  372: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME;
+ 373: 	@API(status = DEPRECATED, since = "6.1")
+ 374: 	@Deprecated(forRemoval = true, since = "6.1")
+ 375: 	public static final String PARALLEL_CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_DYNAMIC_FACTOR_PROPERTY_NAME;
  376: 
  377: 	/**
  378: 	 * Property name used to specify the fully qualified class name of the
- : 	 * {@link ParallelExecutionConfigurationStrategy} to be used for the
- : 	 * {@code custom} configuration strategy: {@value}
+ 379: 	 * {@code custom} parallel execution configuration strategy to be used:
+ 380: 	 * {@value}
  381: 	 *
  382: 	 * @since 5.3
+ 383: 	 * @deprecated Please use
+ 384: 	 * {@link org.junit.jupiter.api.Constants#PARALLEL_CONFIG_CUSTOM_CLASS_PROPERTY_NAME}
+ 385: 	 * instead.
  386: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String PARALLEL_CONFIG_CUSTOM_CLASS_PROPERTY_NAME = JupiterConfiguration.PARALLEL_CONFIG_PREFIX
- : 			+ CONFIG_CUSTOM_CLASS_PROPERTY_NAME;
+ 387: 	@API(status = DEPRECATED, since = "6.1")
+ 388: 	@Deprecated(forRemoval = true, since = "6.1")
+ 389: 	public static final String PARALLEL_CONFIG_CUSTOM_CLASS_PROPERTY_NAME = org.junit.jupiter.api.Constants.PARALLEL_CONFIG_CUSTOM_CLASS_PROPERTY_NAME;
  390: 
  391: 	/**
  392: 	 * Property name used to set the default timeout for all testable and
  393: 	 * lifecycle methods: {@value}.
  394: 	 *
  395: 	 * @see Timeout#DEFAULT_TIMEOUT_PROPERTY_NAME
+ 396: 	 * @deprecated Please use
+ 397: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TIMEOUT_PROPERTY_NAME}
+ 398: 	 * instead.
  399: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TIMEOUT_PROPERTY_NAME;
+ 400: 	@API(status = DEPRECATED, since = "6.1")
+ 401: 	@Deprecated(forRemoval = true, since = "6.1")
+ 402: 	public static final String DEFAULT_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TIMEOUT_PROPERTY_NAME;
  403: 
  404: 	/**
  405: 	 * Property name used to set the default timeout for all testable methods: {@value}.
  406: 	 *
  407: 	 * @see Timeout#DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME
+ 408: 	 * @deprecated Please use
+ 409: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME}
+ 410: 	 * instead.
  411: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 412: 	@API(status = DEPRECATED, since = "6.1")
+ 413: 	@Deprecated(forRemoval = true, since = "6.1")
+ 414: 	public static final String DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TESTABLE_METHOD_TIMEOUT_PROPERTY_NAME;
  415: 
  416: 	/**
  417: 	 * Property name used to set the default timeout for all
  418: 	 * {@link Test @Test} methods: {@value}.
  419: 	 *
  420: 	 * @see Timeout#DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME
+ 421: 	 * @deprecated Please use
+ 422: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME}
+ 423: 	 * instead.
  424: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME;
+ 425: 	@API(status = DEPRECATED, since = "6.1")
+ 426: 	@Deprecated(forRemoval = true, since = "6.1")
+ 427: 	public static final String DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_METHOD_TIMEOUT_PROPERTY_NAME;
  428: 
  429: 	/**
  430: 	 * Property name used to set the default timeout for all
  431: 	 * {@link TestTemplate @TestTemplate} methods: {@value}.
  432: 	 *
  433: 	 * @see Timeout#DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME
+ 434: 	 * @deprecated Please use
+ 435: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME}
+ 436: 	 * instead.
  437: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 438: 	@API(status = DEPRECATED, since = "6.1")
+ 439: 	@Deprecated(forRemoval = true, since = "6.1")
+ 440: 	public static final String DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_TEMPLATE_METHOD_TIMEOUT_PROPERTY_NAME;
  441: 
  442: 	/**
  443: 	 * Property name used to set the default timeout for all
  444: 	 * {@link TestFactory @TestFactory} methods: {@value}.
  445: 	 *
  446: 	 * @see Timeout#DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME
+ 447: 	 * @deprecated Please use
+ 448: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME}
+ 449: 	 * instead.
  450: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME;
+ 451: 	@API(status = DEPRECATED, since = "6.1")
+ 452: 	@Deprecated(forRemoval = true, since = "6.1")
+ 453: 	public static final String DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_FACTORY_METHOD_TIMEOUT_PROPERTY_NAME;
  454: 
  455: 	/**
  456: 	 * Property name used to set the default timeout for all lifecycle methods: {@value}.
  457: 	 *
  458: 	 * @see Timeout#DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME
+ 459: 	 * @deprecated Please use
+ 460: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME}
+ 461: 	 * instead.
  462: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME;
+ 463: 	@API(status = DEPRECATED, since = "6.1")
+ 464: 	@Deprecated(forRemoval = true, since = "6.1")
+ 465: 	public static final String DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_LIFECYCLE_METHOD_TIMEOUT_PROPERTY_NAME;
  466: 
  467: 	/**
  468: 	 * Property name used to set the default timeout for all
  469: 	 * {@link BeforeAll @BeforeAll} methods: {@value}.
  470: 	 *
  471: 	 * @see Timeout#DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME
+ 472: 	 * @deprecated Please use
+ 473: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME}
+ 474: 	 * instead.
  475: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
+ 476: 	@API(status = DEPRECATED, since = "6.1")
+ 477: 	@Deprecated(forRemoval = true, since = "6.1")
+ 478: 	public static final String DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_BEFORE_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
  479: 
  480: 	/**
  481: 	 * Property name used to set the default timeout for all
  482: 	 * {@link BeforeEach @BeforeEach} methods: {@value}.
  483: 	 *
  484: 	 * @see Timeout#DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME
+ 485: 	 * @deprecated Please use
+ 486: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME}
+ 487: 	 * instead.
  488: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
+ 489: 	@API(status = DEPRECATED, since = "6.1")
+ 490: 	@Deprecated(forRemoval = true, since = "6.1")
+ 491: 	public static final String DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_BEFORE_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
  492: 
  493: 	/**
  494: 	 * Property name used to set the default timeout for all
  495: 	 * {@link AfterEach @AfterEach} methods: {@value}.
  496: 	 *
  497: 	 * @see Timeout#DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME
+ 498: 	 * @deprecated Please use
+ 499: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME}
+ 500: 	 * instead.
  501: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
+ 502: 	@API(status = DEPRECATED, since = "6.1")
+ 503: 	@Deprecated(forRemoval = true, since = "6.1")
+ 504: 	public static final String DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_AFTER_EACH_METHOD_TIMEOUT_PROPERTY_NAME;
  505: 
  506: 	/**
  507: 	 * Property name used to set the default timeout for all
  508: 	 * {@link AfterAll @AfterAll} methods: {@value}.
  509: 	 *
  510: 	 * @see Timeout#DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME
+ 511: 	 * @deprecated Please use
+ 512: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME}
+ 513: 	 * instead.
  514: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME = Timeout.DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
+ 515: 	@API(status = DEPRECATED, since = "6.1")
+ 516: 	@Deprecated(forRemoval = true, since = "6.1")
+ 517: 	public static final String DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_AFTER_ALL_METHOD_TIMEOUT_PROPERTY_NAME;
  518: 
  519: 	/**
  520: 	 * Property name used to configure whether timeouts are applied to tests: {@value}.
  521: 	 *
  522: 	 * @see Timeout#TIMEOUT_MODE_PROPERTY_NAME
+ 523: 	 * @deprecated Please use
+ 524: 	 * {@link org.junit.jupiter.api.Constants#TIMEOUT_MODE_PROPERTY_NAME}
+ 525: 	 * instead.
  526: 	 */
- : 	@API(status = STABLE, since = "5.10")
- : 	public static final String TIMEOUT_MODE_PROPERTY_NAME = Timeout.TIMEOUT_MODE_PROPERTY_NAME;
+ 527: 	@API(status = DEPRECATED, since = "6.1")
+ 528: 	@Deprecated(forRemoval = true, since = "6.1")
+ 529: 	public static final String TIMEOUT_MODE_PROPERTY_NAME = org.junit.jupiter.api.Constants.TIMEOUT_MODE_PROPERTY_NAME;
  530: 
  531: 	/**
  532: 	 * Property name used to set the default method orderer class name: {@value}
  533: 	 *
  534: 	 * @see MethodOrderer#DEFAULT_ORDER_PROPERTY_NAME
+ 535: 	 * @deprecated Please use
+ 536: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME}
+ 537: 	 * instead.
  538: 	 */
- : 	@API(status = STABLE, since = "5.9")
- : 	public static final String DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME = MethodOrderer.DEFAULT_ORDER_PROPERTY_NAME;
+ 539: 	@API(status = DEPRECATED, since = "6.1")
+ 540: 	@Deprecated(forRemoval = true, since = "6.1")
+ 541: 	public static final String DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_METHOD_ORDER_PROPERTY_NAME;
  542: 
  543: 	/**
  544: 	 * Property name used to set the default class orderer class name: {@value}
  545: 	 *
  546: 	 * @see ClassOrderer#DEFAULT_ORDER_PROPERTY_NAME
+ 547: 	 * @deprecated Please use
+ 548: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_CLASS_ORDER_PROPERTY_NAME}
+ 549: 	 * instead.
  550: 	 */
- : 	@API(status = STABLE, since = "5.9")
- : 	public static final String DEFAULT_TEST_CLASS_ORDER_PROPERTY_NAME = ClassOrderer.DEFAULT_ORDER_PROPERTY_NAME;
+ 551: 	@API(status = DEPRECATED, since = "6.1")
+ 552: 	@Deprecated(forRemoval = true, since = "6.1")
+ 553: 	public static final String DEFAULT_TEST_CLASS_ORDER_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_CLASS_ORDER_PROPERTY_NAME;
  554: 
  555: 	/**
  556: 	 * Property name used to set the default timeout thread mode.
  557: 	 *
  558: 	 * @since 5.9
  559: 	 * @see Timeout
  560: 	 * @see Timeout.ThreadMode
+ 561: 	 * @deprecated Please use
+ 562: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME}
+ 563: 	 * instead.
  564: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME = Timeout.DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME;
+ 565: 	@API(status = DEPRECATED, since = "6.1")
+ 566: 	@Deprecated(forRemoval = true, since = "6.1")
+ 567: 	public static final String DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TIMEOUT_THREAD_MODE_PROPERTY_NAME;
  568: 
  569: 	/**
  570: 	 * Property name used to set the default factory for temporary directories created via
  571: 	 * the {@link TempDir @TempDir} annotation: {@value}
  572: 	 *
  573: 	 * @since 5.10
  574: 	 * @see TempDir#DEFAULT_FACTORY_PROPERTY_NAME
+ 575: 	 * @deprecated Please use
+ 576: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEMP_DIR_FACTORY_PROPERTY_NAME}
+ 577: 	 * instead.
  578: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String DEFAULT_TEMP_DIR_FACTORY_PROPERTY_NAME = TempDir.DEFAULT_FACTORY_PROPERTY_NAME;
+ 579: 	@API(status = DEPRECATED, since = "6.1")
+ 580: 	@Deprecated(forRemoval = true, since = "6.1")
+ 581: 	public static final String DEFAULT_TEMP_DIR_FACTORY_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEMP_DIR_FACTORY_PROPERTY_NAME;
  582: 
  583: 	/**
  584: 	 * Property name used to set the default extension context scope for
  585: 	 * extensions that participate in test instantiation: {@value}
  586: 	 *
  587: 	 * @since 5.12
  588: 	 * @see org.junit.jupiter.api.extension.TestInstantiationAwareExtension
+ 589: 	 * @deprecated Please use
+ 590: 	 * {@link org.junit.jupiter.api.Constants#DEFAULT_TEST_CLASS_INSTANCE_CONSTRUCTION_EXTENSION_CONTEXT_SCOPE_PROPERTY_NAME}
+ 591: 	 * instead.
  592: 	 */
- : 	@API(status = MAINTAINED, since = "5.13.3")
- : 	public static final String DEFAULT_TEST_CLASS_INSTANCE_CONSTRUCTION_EXTENSION_CONTEXT_SCOPE_PROPERTY_NAME = ExtensionContextScope.DEFAULT_SCOPE_PROPERTY_NAME;
+ 593: 	@API(status = DEPRECATED, since = "6.1")
+ 594: 	@Deprecated(forRemoval = true, since = "6.1")
+ 595: 	public static final String DEFAULT_TEST_CLASS_INSTANCE_CONSTRUCTION_EXTENSION_CONTEXT_SCOPE_PROPERTY_NAME = org.junit.jupiter.api.Constants.DEFAULT_TEST_CLASS_INSTANCE_CONSTRUCTION_EXTENSION_CONTEXT_SCOPE_PROPERTY_NAME;
  596: 
  597: 	private Constants() {
  598: 		/* no-op */
  599: 	}
  600: 
  601: }
```

**The reviewer's comment:**

> The deprecated field now delegates to org.junit.jupiter.api.Constants instead of being a direct alias. This could break compatibility if the target constant has different behavior.

**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________

---
