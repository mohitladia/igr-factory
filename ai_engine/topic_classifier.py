from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class TopicProfile:
    family: str
    format_name: str
    required_concepts: tuple[str, ...]
    teaching_flow: tuple[str, ...]

RULES = [
    (r"\b(two\s*sum|three\s*sum|anagram|valid\s*anagram|group\s*anagrams|palindrome|valid\s*palindrome|valid\s*parentheses|parentheses|binary\s*search|linked\s*list|lru\s*cache|tree|graph|bfs|dfs|dynamic\s*programming|leetcode|dsa|array|string|hashmap|two\s*pointers|sliding\s*window|prefix\s*sum|merge\s*intervals|trapping\s*rain\s*water|coin\s*change)\b",
     TopicProfile("dsa", "algorithm_walkthrough", ("problem", "baseline_vs_optimal", "mental_model", "dry_run", "complexity"), ("hook", "problem", "baseline", "optimized_approach", "dry_run", "complexity", "takeaway"))),
    (r"\b(kafka|rabbitmq|sqs|redis\s*streams|event\s*streaming|message\s*queue)\b",
     TopicProfile("distributed_messaging", "event_streaming_explainer", ("producer", "consumer", "delivery_or_storage_semantics"), ("hook", "problem", "core_model", "data_flow", "reliability", "use_cases", "takeaway"))),
    (r"\b(redis|caching|cache|memcached)\b",
     TopicProfile("caching", "caching_system_explainer", ("cache_read", "cache_write", "eviction_or_expiry"), ("hook", "problem", "cache_flow", "consistency_or_eviction", "tradeoffs", "use_cases", "takeaway"))),
    (r"\b(spring\s*boot|spring\s*framework|dependency\s*injection|hibernate|jpa)\b",
     TopicProfile("backend_framework", "request_lifecycle_explainer", ("request_flow", "dependency_injection", "configuration"), ("hook", "problem", "core_concept", "request_lifecycle", "under_the_hood", "use_cases", "takeaway"))),
    (r"\b(java|jvm|garbage\s*collection|multithreading|concurrency)\b",
     TopicProfile("programming_language", "runtime_concept_explainer", ("core_concept", "execution_model", "tradeoff"), ("hook", "problem", "mental_model", "execution", "example", "tradeoffs", "takeaway"))),
    (r"\b(system\s*design|microservices|load\s*balancer|database\s*sharding|sharding|consistent\s*hashing|hashing\s*ring|rate\s*limiter|api\s*gateway|horizontal\s*scaling|vertical\s*scaling|scaling|autoscaling|cap\s*theorem|cdn|webhook|graphql|docker|kubernetes)\b",
     TopicProfile("system_design", "architecture_tradeoff_explainer", ("requirements", "architecture", "tradeoffs"), ("hook", "problem", "requirements", "architecture", "request_flow", "tradeoffs", "takeaway"))),
]

def classify_topic(topic: str) -> TopicProfile:
    normalized = re.sub(r"[_]+", " ", topic.lower()).strip()
    for pattern, profile in RULES:
        if re.search(pattern, normalized):
            return profile
    return TopicProfile("general_technical", "concept_explainer",
        ("definition", "how_it_works", "example", "tradeoffs"),
        ("hook", "problem_or_motivation", "definition", "how_it_works", "example", "tradeoffs", "takeaway"))
