from enum import Enum
from typing import Type, Dict

class PromptType(str, Enum):
    CODING = "Coding"
    BUSINESS_ANALYST = "BusinessAnalyst"

class PromptStore:
    def __init__(self, prompt_type: PromptType):
        self.prompt_type = prompt_type

    def format_prompt(self, question: str, context: str) -> str:
        return f"""## 🧠 AI Assistant

> You are an AI assistant providing answers based on the provided context.

---

### 🔒 Constraints

* Use **only** the content in the `Context` section below.
* **Do not** make assumptions or use external knowledge.
* **Do not** hallucinate information.

---

### 🗃️ Context:

```
{context}
```

---

### ❓ Question:

```
{question}
```

---

### ✅ Answer:
"""

class CodingPromptStore(PromptStore):
    def format_prompt(self, question: str, context: str) -> str:
        return f"""## 🧠 Coding AI Assistant

> You are a **coding assistant**, helping with code, debugging, and programming questions.

---

### 🔒 Constraints

* Use **only** the content in the `Context` section below.
* **Do not** assume knowledge outside of the context.
* Provide correct and concise coding guidance.

---

### 🗃️ Context:

```
{context}
```

---

### ❓ Question:

```
{question}
```

---

### ✅ Answer:
"""

class BusinessAnalystPromptStore(PromptStore):
    def format_prompt(self, question: str, context: str) -> str:
        return f"""## 🧠 Business Analyst AI Assistant

> You are a **business analyst assistant**, providing insights, analysis, and recommendations.

---

### 🔒 Constraints

* Use **only** the content in the `Context` section below.
* **Do not** assume knowledge outside of the context.
* Provide clear and actionable business insights.

---

### 🗃️ Context:

```
{context}
```

---

### ❓ Question:

```
{question}
```

---

### ✅ Answer:
"""

class PromptStoreFactory:
    _store_map: Dict[PromptType, Type[PromptStore]] = {
        PromptType.CODING: CodingPromptStore,
        PromptType.BUSINESS_ANALYST: BusinessAnalystPromptStore,
    }

    @classmethod
    def create(cls, prompt_type: PromptType) -> PromptStore:
        store_cls = cls._store_map.get(prompt_type)
        if not store_cls:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")
        return store_cls(prompt_type)