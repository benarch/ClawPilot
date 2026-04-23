---
name: "hebrew-decode"
description: "Automatically decode Hebrew characters that were accidentally typed instead of English, using the Hebrew-English keyboard layout mapping. Use this skill when a user types a sentence in Hebrew characters that appear to be mistyped English (e.g. \"ים׳ שרק טםו?\" → \"how are you?\"). Also understand and respond to genuine Hebrew messages. Triggers when a message contains Hebrew characters."
---

# hebrew-keyboard-decode

**Skill:** `hebrew-keyboard-decode`
**Description:** Automatically decode Hebrew characters that were accidentally typed instead of English, using the Hebrew-English keyboard layout mapping. Use this skill when a user types a sentence in Hebrew characters but clearly intended English (e.g. "ים׳ שרק טםו?" → "how are you?"). Also understand and respond to genuine Hebrew messages. Triggers when a message contains Hebrew characters that appear to be mistyped English.

---

## How to Detect Mistyped Hebrew

If a Hebrew-character message doesn't make sense as Hebrew, assume the user accidentally had their keyboard in Hebrew mode. Decode it letter-by-letter using the keyboard map and respond to the English meaning.

If the message makes sense as genuine Hebrew, respond in Hebrew.

---

## Hebrew → English Keyboard Map

| Hebrew | English |
|--------|---------|
| ק | e |
| ר | r |
| א | t |
| ט | t |
| ו | u |
| י | h |
| כ | x |
| ע | g |
| ז | z |
| ש | a |
| ד | c |
| ף | ; |
| ך | l |
| ת | , |
| נ | b |
| פ | p |
| ן | i |
| ם | o |
| ל | k |
| ח | j |
| ג | d |
| ב | v |
| ס | s |
| צ | m |
| מ | n |
| ׳ | y |
| ה | v |
| ץ | . |

Space and punctuation remain as-is.

---

## Examples

| Hebrew Input | Decoded English |
|---|---|
| `ים׳ שרק טםו גםןמע?` | `how are you doing?` |
| `טקד` | `tui` |
| `ן ׳םוךג ךןלק אם גקהקךםפ שמ שפפ` | `i would like to develop an app` |

---

## Behaviour

Decode the message silently — do not explain the decoding process unless asked. Just respond to what the user meant to say. If decoding produces a near-match but not a perfect sentence, use context to infer the most likely intended meaning and respond accordingly.
