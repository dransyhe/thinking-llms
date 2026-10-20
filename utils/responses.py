def extract_thinking_process(response):
    """Extract the model's "thinking" span from a raw response string.

    Many of our generated responses include a chain-of-thought segment wrapped in
    `<think> ... </think>` tags, often preceded by an instruction preamble.

    Open-Reasoner-Zero outputs can be messy: the string may contain multiple
    `<think>` blocks (including empty trailing ones like `Assistant: <think> </think>`).
    The goal here is to choose a *stable* start marker that corresponds to the
    main reasoning, then return text up to the next `</think>` (or end of text).

    Selection policy (as requested):
    - If there's **no** `<think>`, start right after the last ChatML assistant header
      (`<|im_start|>assistant\n`) if present, else at 0.
    - If there's **exactly one** `<think>`, start right after it.
    - If there are **multiple** `<think>`:
      - Look for occurrences of the Open-Reasoner-Zero marker `"Assistant: <think>"`.
      - If there is exactly one such marker, use it.
      - If there are multiple, use the *first* (leftmost) one.
      - (If none exist, fall back to the last `<think>` to preserve prior behavior
        on non-ORZ formats that may include multiple `<think>` tags.)
    """

    think_tag = "<think>"
    end_tag = "</think>"
    orz_marker = "Assistant: <think>"
    chatml_assistant_marker = "<|im_start|>assistant\n"

    n_think = response.count(think_tag)

    # 1) No <think>: treat the assistant turn as "thinking-like" content. Non-thinking
    #    chat models (e.g. Qwen3-*-Instruct-2507) emit no tags, and the vLLM response
    #    string starts with the chat-templated prompt, so skip past the last assistant
    #    header when there is one; otherwise use the entire string.
    if n_think == 0:
        assistant_start = response.rfind(chatml_assistant_marker)
        think_start = 0 if assistant_start == -1 else assistant_start + len(chatml_assistant_marker)

    # 2) Exactly one <think>: take the only block.
    elif n_think == 1:
        think_start = response.find(think_tag) + len(think_tag)

    # 3) Multiple <think>: prefer ORZ's "Assistant: <think>" anchor when possible.
    else:
        first_orz = response.find(orz_marker)
        if first_orz != -1:
            think_start = first_orz + len(orz_marker)
        else:
            # Backwards-compatible fallback: the previous implementation chose the
            # last <think> block. This keeps behavior unchanged for other formats.
            think_start = response.rfind(think_tag) + len(think_tag)

    # Always consume until the first closing tag after our chosen start.
    think_end = response.find(end_tag, think_start)
    if think_end == -1:
        think_end = len(response)

    return response[think_start:think_end].strip()