import re

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "ought",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about", "up",
    "its", "it", "he", "she", "they", "we", "you", "me", "my", "your",
    "his", "her", "their", "our", "this", "that", "these", "those", "what",
    "which", "who", "whom", "whose", "also", "any", "much", "many",
    "like", "well", "back", "even", "still", "new", "one", "two",
    "get", "got", "set", "use", "used", "using", "make", "made",
}

CODE_KEYWORDS = {
    "if", "else", "elif", "for", "while", "return", "import", "from",
    "class", "def", "const", "let", "var", "function", "try", "except",
    "catch", "finally", "throw", "new", "delete", "typeof", "instanceof",
    "void", "null", "none", "true", "false", "break", "continue",
    "switch", "case", "default", "yield", "async", "await", "static",
    "public", "private", "protected", "extends", "implements",
    "super", "self", "this", "print", "console", "require", "export",
    "enum", "struct", "typedef", "include", "pragma", "namespace",
}

TECH_TERMS = {
    "api", "sdk", "http", "https", "url", "uri", "json", "xml", "html",
    "css", "javascript", "typescript", "python", "java", "node", "rust",
    "react", "vue", "angular", "webpack", "vite", "npm", "yarn", "pnpm",
    "docker", "kubernetes", "git", "github", "gitlab", "repository",
    "deploy", "deployment", "server", "client", "frontend", "backend",
    "database", "query", "schema", "migration", "orm", "sql", "nosql",
    "cache", "redis", "mongodb", "postgresql", "mysql", "sqlite",
    "authentication", "authorization", "token", "jwt", "oauth", "session",
    "middleware", "router", "endpoint", "controller", "model", "view",
    "component", "module", "package", "library", "framework", "plugin",
    "callback", "promise", "observable", "stream", "buffer", "socket",
    "thread", "process", "daemon", "kernel", "binary", "compiler",
    "interpreter", "runtime", "virtual", "machine", "container",
    "cluster", "proxy", "gateway", "webhook", "pipeline", "cicd",
    "algorithm", "recursion", "iteration", "complexity", "optimization",
    "parameter", "argument", "variable", "constant", "boolean", "integer",
    "array", "object", "tuple", "dictionary", "hashmap", "hashtable",
    "stack", "queue", "tree", "graph", "heap", "encryption", "protocol",
    "request", "response", "header", "payload", "status", "exception",
    "handler", "listener", "event", "trigger", "template", "render",
    "parse", "serialize", "deserialize", "dependency", "injection",
    "singleton", "factory", "pattern", "refactor", "debug", "testing",
    "integration", "coverage", "lint", "format", "compile", "bundle",
    "config", "configuration", "environment", "production", "staging",
    "localhost", "port", "domain", "host", "cors", "synchronous",
    "asynchronous", "concurrent", "parallel", "mutex", "deadlock",
    "semaphore", "branch", "merge", "commit", "push", "pull", "fetch",
    "clone", "fork", "rebase", "conflict", "diff", "scaffold",
    "boilerplate", "snippet", "syntax", "semantic", "viewport",
    "responsive", "breakpoint", "flexbox", "gradient", "animation",
    "transition", "transform", "repository", "instance", "interface",
    "abstract", "override", "constructor", "destructor", "inheritance",
    "polymorphism", "encapsulation", "abstraction", "iterator",
    "generator", "decorator", "annotation", "assertion", "benchmark",
    "profiler", "debugger", "transpiler", "minifier", "bundler",
    "linter", "formatter", "sanitizer", "validator", "serializer",
    "middleware", "microservice", "monolith", "serverless", "lambda",
    "orchestration", "provisioning", "terraform", "ansible", "nginx",
    "apache", "cdn", "dns", "ssl", "tls", "certificate", "firewall",
    "loadbalancer", "autoscaling", "monitoring", "alerting", "logging",
    "tracing", "observability", "rollback", "canary", "bluegreen",
}


def _is_code_like(text):
    if re.search(r"[(){}\[\];=<>!&|^~@#$%]", text):
        return True
    if re.search(r"[a-z][A-Z]", text):
        return True
    if re.search(r"_[a-zA-Z]", text) and not text.startswith("_"):
        return True
    if re.search(r"\.\w+\(", text):
        return True
    words = text.lower().split()
    if any(w in CODE_KEYWORDS for w in words):
        return True
    return False


def _classify(text):
    text_lower = text.lower().strip()
    words = text_lower.split()
    if _is_code_like(text):
        return "代码"
    if any(w in TECH_TERMS for w in words):
        return "专业术语"
    return "日常"


def _determine_length(text):
    words = text.strip().split()
    return "单词" if len(words) <= 1 else "短句"


def _is_valid_english(text):
    if len(text) < 3:
        return False
    if re.match(r"^[\d\s\W]+$", text):
        return False
    if re.search(r"[\u4e00-\u9fff]", text):
        return False
    alpha_count = sum(1 for c in text if c.isalpha())
    return alpha_count >= max(2, len(text) * 0.5)


def extract_items(ocr_lines, min_word_length=3, max_phrase_words=8):
    items = []
    seen = set()

    for line in ocr_lines:
        line = line.strip()
        if not line:
            continue

        segments = re.findall(r"[A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*)*", line)

        for segment in segments:
            segment = segment.strip()
            if not _is_valid_english(segment):
                continue

            words = segment.split()

            if len(words) == 1:
                word = words[0]
                word_lower = word.lower()
                if len(word) < min_word_length:
                    continue
                if word_lower in STOP_WORDS:
                    continue
                if word_lower in seen:
                    continue
                seen.add(word_lower)
                items.append({
                    "english": word,
                    "category": _classify(word),
                    "length_type": "单词",
                })

            elif 2 <= len(words) <= max_phrase_words:
                meaningful = [w for w in words if w.lower() not in STOP_WORDS and len(w) >= 2]
                if not meaningful:
                    continue

                phrase = " ".join(words)
                phrase_key = phrase.lower()
                if phrase_key in seen:
                    continue
                seen.add(phrase_key)
                items.append({
                    "english": phrase,
                    "category": _classify(phrase),
                    "length_type": "短句",
                })

                for w in meaningful:
                    w_lower = w.lower()
                    if len(w) >= min_word_length and w_lower not in seen:
                        seen.add(w_lower)
                        items.append({
                            "english": w,
                            "category": _classify(w),
                            "length_type": "单词",
                        })

    return items
