# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **janus-medspacy**, a fork of [medspacy](https://github.com/medspacy/medspacy) - a clinical NLP library built on spaCy. MedSpaCy provides specialized pipeline components for processing clinical/medical text, including sentence segmentation, concept extraction, contextual analysis (negation, uncertainty, temporality), and section detection.

## Common Commands

### Installation
```bash
pip install -e .                    # Editable install
pip install -r requirements/requirements.txt
```

### Testing
```bash
# Run all tests (excluding QuickUMLS span group tests which need separate session)
pytest -k "not test_span_groups and not test_overlapping_spans and not test_multiword_span"

# Run QuickUMLS span group tests separately
pytest -k "test_span_groups or test_overlapping_spans or test_multiword_span"

# Run a single test file
pytest tests/context/test_context_component.py

# Run a single test
pytest tests/test_medspacy.py::TestMedSpaCy::test_default_load
```

### Linting
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Required spaCy Models for Testing
```bash
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_md
python -m spacy download de_core_news_sm
python -m spacy download es_core_news_sm
python -m spacy download pl_core_news_sm
python -m spacy download xx_ent_wiki_sm
```

## Architecture

### Pipeline Components

MedSpaCy extends spaCy with clinical-specific components registered under the `medspacy_` prefix:

| Component | Purpose |
|-----------|---------|
| `medspacy_tokenizer` | Aggressive tokenizer for clinical text (set on `nlp.tokenizer`) |
| `medspacy_pyrush` | PyRuSH-based sentence splitting |
| `medspacy_target_matcher` | Rule-based entity extraction using `TargetRule` |
| `medspacy_context` | ConText algorithm for detecting negation, uncertainty, family history, hypothetical |
| `medspacy_sectionizer` | Section header detection and document segmentation |
| `medspacy_quickumls` | UMLS concept linking via QuickUMLS |
| `medspacy_preprocessor` | Text preprocessing before tokenization |
| `medspacy_postprocessor` | Entity filtering/modification after extraction |
| `medspacy_doc_consumer` | Convert processed docs to structured data |

### Loading Pipelines

```python
import medspacy

# Default components: tokenizer, pyrush, target_matcher, context
nlp = medspacy.load()

# All components
nlp = medspacy.load(medspacy_enable="all")

# Specific components
nlp = medspacy.load(medspacy_enable={"medspacy_target_matcher", "medspacy_sectionizer"})

# With language-specific resources
nlp = medspacy.load(language_code="fr")
```

### Key Modules

- **[medspacy/context/](medspacy/context/)**: ConText implementation for attribute detection. `ConTextRule` defines modifiers; `ConText` component applies them setting span attributes like `is_negated`, `is_uncertain`, `is_historical`, `is_hypothetical`, `is_family`.

- **[medspacy/target_matcher/](medspacy/target_matcher/)**: Entity extraction via `TargetRule` (supports literal strings or spaCy patterns).

- **[medspacy/section_detection/](medspacy/section_detection/)**: Clinical section parsing using `SectionRule` patterns.

- **[medspacy/common/](medspacy/common/)**: Shared base classes (`MedspacyMatcher`, `BaseRule`) used by multiple components.

- **[medspacy/io/](medspacy/io/)**: Database I/O for batch processing (`DbReader`, `DbWriter`, `DocConsumer`).

### Language Resources

Resources are in `resources/{language_code}/`:
- `context_rules.json` - ConText modifier rules
- `section_patterns.json` - Section header patterns
- `rush_rules.tsv` - Sentence boundary rules
- `quickumls/` - UMLS sample databases (platform-specific: POSIX vs Windows)

Supported languages: en, fr, nl, es, pl, pt, it, de (varying rule coverage)

### spaCy Extensions

MedSpaCy registers custom attributes on spaCy objects:
- `Span._.modifiers` - List of ConTextModifier objects affecting the span
- `Span._.is_negated`, `is_uncertain`, `is_historical`, `is_hypothetical`, `is_family`
- `Doc._.context_graph` - ConTextGraph with targets, modifiers, and edges
- `Doc._.sections` - List of detected sections
