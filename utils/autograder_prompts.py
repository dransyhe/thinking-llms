"""
Autograder prompt building utilities for clustering evaluation.
This module contains functions to build the various prompts used in clustering
evaluation including cluster description generation, completeness evaluation,
accuracy evaluation, and semantic orthogonality evaluation.
"""

categories_examples = [
    {
        'title': 'Generating Hypotheses',
        'description': (
            'These sentences introduce a tentative explanation or causal link that could account for '
            'the facts already stated, guiding the rest of the reasoning toward testing or refinement. '
            'Included are speculative "maybe" or "could be" statements that present a single, coherent '
            'possibility, often signaled by modals ("might", "could") or framing phrases ("one explanation is").'
        ),
        'examples': [
            'A likely explanation is that the anomaly arises from sensor drift rather than genuine temperature change.',
            'One possibility is that the agent over-optimizes for short-term reward, ignoring the long-term penalty.',
            'It could be that the unexpected output stems from an off-by-one error in the loop index.',
            "Perhaps the model's poor performance results from covariate shift between the training and test datasets.",
            'A plausible reason is that memory fragmentation slows allocation as the program runs.',
        ]
    },
    {
        'title': 'Expressing Uncertainty',
        'description': (
            'These sentences explicitly acknowledge uncertainty or limitations in the current reasoning state, '
            'signaling awareness of incomplete information or ambiguity without proposing a concrete hypothesis. '
            'Included are clear acknowledgments of uncertainty or ignorance (e.g., "I\'m not sure," "It\'s unclear," '
            '"I can\'t be certain").'
        ),
        'examples': [
            "It's unclear whether the author intended this interpretation.",
            "I'm not sure if the given data is sufficient to draw a conclusion here.",
            "I can't be certain from the provided details alone.",
            "There's insufficient information to determine the exact cause of the discrepancy.",
            "It remains uncertain if the described approach generalizes beyond this particular context.",
        ]
    },
    {
        'title': 'Planning Future Steps',
        'description': (
            'These sentences explicitly lay out the next action(s) the reasoner intends to take, '
            'framing the reasoning as a sequence of ordered steps. Included are forward-looking '
            'statements with temporal markers ("first," "next," "then," "after that," "finally") '
            'that announce but do not yet execute an operation.'
        ),
        'examples': [
            "First, I'll restate the key facts in my own words.",
            "Next, I will compute the correlation between the two variables.",
            "Then I plan to test whether those coefficients remain significant under regularization.",
            "After that, I'll examine edge cases to see if the rule still holds.",
            "Finally, I'll synthesize the evidence into a concise conclusion.",
        ]
    },
    {
        'title': 'Stating Assumptions',
        'description': (
            'These sentences explicitly state a premise that will be treated as true for the remainder of '
            'the reasoning, establishing a temporary foundation on which deductions or calculations will build. '
            'Included are phrases that foreground the assumption—"assume," "suppose," "let\'s posit," '
            '"given that"—without yet evaluating or testing it.'
        ),
        'examples': [
            "Let's assume the training data are independently and identically distributed.",
            "Suppose the network latency remains constant throughout the experiment.",
            "Given that the user's intent is benign, we can skip the security sandbox.",
            "For simplicity, I'll posit that all variables follow a Gaussian prior.",
            "Assume the function is differentiable over the entire real line.",
        ]
    },
    {
        'title': 'Recalling Mathematical Definitions',
        'description': (
            'These sentences retrieve a known fact, formula, or formal definition from memory to serve as a premise '
            'for the upcoming reasoning step, without yet applying or testing it. Included are explicit reminders '
            'such as "by definition," "recall that," or "we know that" followed by a canonical statement or equation. '
        ),
        'examples': [
            "By definition, a prime number has exactly two positive divisors.",
            "Recall that the area of a circle is π r².",
            "We know that entropy is defined as H(X) = −Σ p(x) log p(x).",
            "According to De Morgan's law, ¬(A ∧ B) ≡ ¬A ∨ ¬B.",
            "By Bayes' theorem, P(A | B) = P(B | A) P(A) / P(B).",
        ]
    }
]


# Example categories for --algo labelling: reusable primitives on an algorithm's state, each illustrated
# with sentences from different CLRS algorithms so the labeller generalises across algorithms.
algo_categories_examples = [
    {
        'title': 'Compare Values',
        'description': (
            'These sentences read two specific values from the current state, test their order or equality, and '
            'state which branch the test selects. Nothing stored is changed in the sentence. Included are tests '
            'between concrete elements, keys, distances, characters, or formula shapes. Not included are sentences '
            'that also write the outcome, such as an assignment, shift, or swap (label those by the write), and '
            'tests of whether a loop or search should end.'
        ),
        'examples': [
            'Since 0.519 < 0.885, 0.885 is out of order and the inner loop continues.',
            'A[mid] = 0.436 is greater than the target 0.324, so the target can only be in the left half.',
            "P[3] = 'b' does not match T[7] = 'a', so the current partial match cannot be extended.",
            'The distance through node 2, 0.570, is less than the current dist[4] = 0.910.',
            'The cross product of p1→p2 and p2→p3 is negative, so the turn at p2 is clockwise.',
        ]
    },
    # {
    #     'title': 'Update Best Value',
    #     'description': (
    #         'These sentences replace a value that is already stored with a better candidate, keeping a running '
    #         'minimum, maximum, or best distance or cost. The sentence states the new value and usually the old one. '
    #         'Not included are the comparison when it is a separate sentence (Compare Values) and the first write '
    #         'of a new entry computed from earlier entries (Combine Subproblem Results).'
    #     ),
    #     'examples': [
    #         'dist[4] is lowered from 0.910 to 0.570.',
    #         'best is raised from 0.977 to 1.284, with range [2, 5].',
    #         'key[6] drops from ∞ to 0.142 and parent[6] becomes 3.',
    #         'The smallest value seen so far changes from 0.233 at index 4 to 0.057 at index 7.',
    #         'Relaxing edge (1, 3) lowers d[3] from 0.744 to 0.391.',
    #     ]
    # },
    {
        'title': 'Combine Subproblem Results',
        'description': (
            'These sentences produce a new result for a larger subproblem from results already computed for '
            'smaller ones, such as a table cell or a merged list. The new result is written for the first time. '
            'Not included are replacing a value that was already stored and statements of a '
            'recurrence that are not evaluated for a specific subproblem.'
        ),
        'examples': [
            'c[3][4] = c[2][3] + 1 = 2.',
            'm[1][4] is the minimum over the three split points, 1250, reached at k = 2.',
            'K[3][5] = max(K[2][5], K[2][2] + 0.640) = 1.120.',
            'D[2][3] = 1 + min(D[1][3], D[2][2], D[1][2]) = 2.',
            'Merging [0.12, 0.58] and [0.31, 0.77] gives [0.12, 0.31, 0.58, 0.77].',
        ]
    },
    # {
    #     'title': 'Expand Frontier',
    #     'description': (
    #         'These sentences add the not-yet-processed neighbours or successors of the current item to the '
    #         'structure that holds pending work, such as a queue, stack, or heap. Not included are choosing or '
    #         'removing the next item to process (Select Next Item) and changes to the distances or keys of those '
    #         'neighbours (Update Best Value).'
    #     ),
    #     'examples': [
    #         "Node 3's unvisited neighbours 5 and 8 are enqueued: queue = [5, 8].",
    #         "Node 6's unvisited neighbours 2 and 7 are pushed onto the stack: stack = [2, 7].",
    #         'Edges (4, 1) and (4, 7) are added to the priority queue.',
    #         'Nodes 2 and 5, which now have in-degree 0, are added to the queue.',
    #         'Neighbours 1 and 4 of node 2 are inserted into the heap.',
    #     ]
    # },
    # {
    #     'title': 'Select Next Item',
    #     'description': (
    #         'These sentences choose or remove the item that will be processed next, from pending work or from a '
    #         'set of candidates. Included are dequeuing, popping, extracting a minimum, taking the next edge, or '
    #         'recursing into a chosen node. Not included are adding items to pending work (Expand Frontier).'
    #     ),
    #     'examples': [
    #         'Node 5 is dequeued, leaving queue = [8].',
    #         'Node 4 is extracted from the heap next.',
    #         'From 6 we recurse into 2, the first unvisited neighbour.',
    #         'The lightest remaining edge, (2, 9), is taken next.',
    #         '9 is popped from the stack and becomes the current node.',
    #     ]
    # },
    {
        'title': 'Move or Swap Elements',
        'description': (
            'These sentences change the position of one or more elements in an array, list, or heap. Included are '
            'shifts, swaps, and placing an element at its final position. Not included are the comparison that '
            'triggers the move when it is a separate sentence.'
        ),
        'examples': [
            '0.885 is shifted one position right, to index 4.',
            'A[2] and A[3] are swapped, giving [0.12, 0.31, 0.58, 0.77].',
            '0.910 is swapped with its parent 0.402 and moves up to index 1.',
            'The pivot 0.461 is placed at its final position, index 3.',
            '0.773 is swapped with A[6], moving it into the right partition.',
        ]
    },
    # {
    #     'title': 'Check Stopping Condition',
    #     'description': (
    #         'These sentences test whether a loop, recursion, search, or proof should end and state whether it '
    #         'stops or continues. Included are checks that a range is empty, pending work is exhausted, a pass made '
    #         'no changes, a count is reached, or a goal is derived. Not included are the final answer itself and '
    #         'comparisons that choose a branch inside the loop (Compare Values).'
    #     ),
    #     'examples': [
    #         'Now low = 5 > high = 4, so the search loop ends.',
    #         'No swaps occurred in this pass, so no further passes are needed.',
    #         'The queue is empty, so the traversal stops.',
    #         '|V| − 1 = 7 rounds of relaxation are done, so the loop ends.',
    #         'The derived formula matches the goal R, so the proof is complete.',
    #     ]
    # },
]

def build_category_examples_text(n_categories_examples=5, categories=None,
                                  header="Here are some example categories to help guide your analysis:"):
    """Format the first n_categories_examples entries of categories (default categories_examples) as prompt guidance ("" if none)."""
    categories = categories_examples if categories is None else categories
    selected_examples = categories[:n_categories_examples] if n_categories_examples > 0 else []
    if not selected_examples:
        return ""
    category_examples_text = f"{header}\n\n"
    for i, category in enumerate(selected_examples):
        category_examples_text += f"**Example Category {i+1}: {category['title']}**\n"
        category_examples_text += f"Description: {category['description']}\n"
        category_examples_text += "Examples:\n"
        for example in category['examples']:
            category_examples_text += f"- {example}\n"
        category_examples_text += "\n"
    return category_examples_text


def build_cluster_description_prompt(examples, trace_examples_text="", n_categories_examples=5):
    """
    Build a prompt for generating cluster descriptions.
    
    Args:
        examples (list): List of example sentences from the cluster
        trace_examples_text (str, optional): Full reasoning trace examples to include
        n_categories_examples (int, optional): Number of category examples to include as guidance
        
    Returns:
        str: Formatted prompt for cluster description generation
    """
    prompt = f"""Analyze the following {len(examples)} sentences from an LLM reasoning trace. These sentences are grouped into a cluster based on their similar role or function in the reasoning process.

Your task is to identify the precise cognitive function these sentences serve in the reasoning process. Consider the reasoning strategy or cognitive operation being performed."""

    if trace_examples_text:
        prompt += f"\n{trace_examples_text}"

    prompt += f"""

Sentences:
'''
{chr(10).join([f"- {example}" for example in examples])}
'''

Look for:
- Shared reasoning strategies or cognitive mechanisms
- Common linguistic patterns or structures
- Functional role within the overall reasoning process"""

    category_examples_text = build_category_examples_text(n_categories_examples)
    if category_examples_text:
        prompt += f"\n\n{category_examples_text}"

    prompt += """

Your response should be in this exact format:
Title: [crisp, single-concept title without slashes, parentheses, or compound phrases]
Description: [3-4 sentences explaining (1) the specific reasoning process this cluster represents, (2) what is INCLUDED in this category, (3) what is NOT INCLUDED in this category]

Guidelines for titles:
- Use simple, clear nouns or verb phrases
- Avoid slashes (/) and parentheses ()
- Capture one core reasoning concept

Guidelines for descriptions:
- Focus on the specific cognitive or reasoning function
- Avoid abstracting too much from the specific examples
- Mention specific phrases or words that are common in the examples
- Be precise enough that someone could reliably identify new examples of this reasoning function.

In summary, the description should be as sharp and specific as possible, and the title should be as simple and abstractq as possible.
"""
    
    return prompt


def build_algo_trace_examples_text(traces):
    """Format (category, question, trace) solutions as context for build_algo_cluster_description_prompt ("" if none)."""
    if not traces:
        return ""
    text = "Here are some full solutions, each shown with the problem it answers, to show the context these sentences come from:\n'''\n"
    for i, (category, question, trace) in enumerate(traces):
        text += f"PROBLEM {i+1} ({category}):\n{question}\n\nSOLUTION {i+1}:\n{trace}\n\n"
    return text + "'''"


def build_algo_cluster_description_prompt(examples, trace_examples_text="", n_categories_examples=5):
    prompt = f"""Analyze the following {len(examples)} sentences from step-by-step solutions 
    in which an LLM executes classical algorithms. 
    These sentences are grouped into a cluster based on they perform similar algorithmic functions 
    in the reasoning process.

Your task is to identify the reusable algorithmic primitive these sentences carry out: an
elementary operation on the algorithm's state that is not tied to any one particular algorithm but 
underlies all sentences of the cluster across algorithms."""

    if trace_examples_text:
        prompt += f"\n\n{trace_examples_text}"

    prompt += f"""

Sentences:
'''
{chr(10).join([f"- {example}" for example in examples])}
'''

Look for:
- The elementary operation the sentences perform on the algorithm's state
- The same operation appearing across different algorithms, inputs, and wordings
- The granularity of a single step, not a whole phase or the whole algorithm

Ignore what the sentences share only in algorithm, data values, formatting (Markdown,
LaTeX, lists), or phrasing. If they share no common primitive, say so."""

    category_examples_text = build_category_examples_text(
        n_categories_examples, algo_categories_examples,
        header="Here are some example primitives to illustrate the intended granularity and style "
    )
    if category_examples_text:
        prompt += f"\n\n{category_examples_text}"

    prompt += """
Your response should be in this exact format:
Title: [crisp verb phrase naming one primitive, without slashes, parentheses, or compound phrases]
Description: [3-4 sentences explaining (1) the primitive this cluster represents, including what state it reads and what it changes or produces, (2) what is INCLUDED in this category, (3) what is NOT INCLUDED in this category]

Guidelines for titles:
- Use a simple verb phrase that names an operation (e.g., "Compare Values", not "Insertion Sort Step")
- Avoid slashes (/) and parentheses ()
- Avoid algorithm names unless the primitive only occurs in that algorithm
- Capture one primitive
- If there is no shared primitive, use the title "No Shared Primitive"

Guidelines for descriptions:
- State the primitive so it applies to any algorithm in which it occurs
- Stay grounded in what the example sentences actually do
- Mention specific phrases or notation only as cues, not as the definition
- Be precise enough that someone could reliably identify new instances of this
  primitive, including in other algorithms.
"""

    return prompt


def build_accuracy_autograder_prompt(title, description, sentences_text):
    """
    Build a prompt for accuracy autograding (binary classification).
    
    Args:
        title (str): Category title
        description (str): Category description
        sentences_text (str): Formatted text with numbered sentences to classify
        
    Returns:
        str: Formatted prompt for binary accuracy evaluation
    """
    return f"""# Task: Binary Classification of Reasoning Sentences by Function

You are an expert at analyzing the *function* of sentences within a longer chain of reasoning. Your task is to determine if each sentence below performs the specific cognitive or procedural role described.

**Core Principle:** Do not focus on the surface-level topic of the sentence. Instead, abstract away from the specific content and ask: "What *job* is this sentence doing in the reasoning trace?"

## Category Description:
Title: {title}
Description: {description}

## Sentences to Classify:
{sentences_text}

## Instructions:
1. For each sentence, identify its functional role in a potential reasoning process.
2. Compare this role to the category description provided.
3. If the sentence's function matches the description, assign "Yes". Importantly, a sentence might not match a description word-for-word, but it might serve the same underlying purpose.
4. If the sentence's function does not align with the category, assign it "No".
5. Respond with "Yes" or "No" for each sentence.

## Response Format:
Your response must follow this exact JSON format:
```json
{{
  "classifications": [
    {{
      "sentence_id": <sentence idx>,
      "explanation": "Brief explanation of your reasoning",
      "belongs_to_category": "Yes" or "No"
    }},
    ... (repeat for all sentences)
  ]
}}
```

Only include the JSON object in your response, with no additional text before or after.
"""


def build_semantic_orthogonality_prompt(title1, description1, title2, description2):
    """
    Build a prompt for semantic orthogonality evaluation.
    
    Args:
        title1 (str): First category title
        description1 (str): First category description
        title2 (str): Second category title  
        description2 (str): Second category description
        
    Returns:
        str: Formatted prompt for semantic similarity evaluation
    """
    return f"""# Task: Semantic Similarity Evaluation

You are an expert at analyzing the semantic similarity between different reasoning functions. Your task is to evaluate how similar two categories of reasoning sentences are in terms of their underlying cognitive or functional purpose.

## Category 1:
Title: {title1}
Description: {description1}

## Category 2:
Title: {title2}
Description: {description2}

## Instructions:
Rate the semantic similarity between these two categories on a scale from 0 to 10, where:
- 0 = Completely different reasoning functions
- 5 = Somewhat related but distinct functions
- 10 = Essentially the same reasoning function, just described differently

Consider:
1. The underlying cognitive process or reasoning operation
2. The functional role within a reasoning trace
3. Whether sentences from one category could reasonably belong to the other

Focus on functional similarity rather than surface-level word overlap.

## Response Format:
Your response must follow this exact JSON format:
```json
{{
  "explanation": "Brief explanation of your reasoning for this score",
  "similarity_score": <integer from 0-10>
}}
```

Only include the JSON object in your response, with no additional text before or after.
"""


def format_categories_text(categories):
    """
    Helper function to format categories for prompt inclusion.
    
    Args:
        categories (list): List of tuples (cluster_id, title, description)
        
    Returns:
        str: Formatted categories text for prompts
    """
    return "\n\n".join([f"Category {cluster_id}: {title}\nDescription: {description}" 
                       for cluster_id, title, description in categories])


def format_sentences_text(sentences, start_idx=0):
    """
    Helper function to format sentences for prompt inclusion.
    
    Args:
        sentences (list): List of sentences to format
        start_idx (int): Starting index for sentence numbering
        
    Returns:
        str: Formatted sentences text for prompts
    """
    return "\n\n".join([f"Sentence {start_idx + i}: {sentence}" 
                       for i, sentence in enumerate(sentences)])


def format_sentences_text_simple(sentences):
    """
    Helper function to format sentences for prompt inclusion (simple numbering from 0).
    
    Args:
        sentences (list): List of sentences to format
        
    Returns:
        str: Formatted sentences text for prompts
    """
    return chr(10).join([f"Sentence {i}: {sentence}" for i, sentence in enumerate(sentences)]) 


def build_completeness_autograder_prompt(sentence, title, description):
    """
    Build a prompt for completeness evaluation of how well a sentence fits its assigned cluster.
    
    Args:
        sentence (str): The sentence to evaluate
        title (str): Title of the assigned cluster
        description (str): Description of the assigned cluster
        
    Returns:
        str: Formatted prompt for completeness evaluation
    """
    return f"""You are an expert at analyzing how well individual sentences match their assigned reasoning function categories. Your task is to evaluate how well a given sentence exemplifies the specific cognitive or procedural role described in its assigned category.

# Sentence to Evaluate:
{sentence}

# Assigned Category:
Title: {title}
Description: {description}

# Instructions:
1. Carefully analyze the sentence's content and the functional role it might display in a reasoning process.
2. Compare this content and role to the category description provided.
3. Consider how well the sentence matches the category description.
4. Provide a brief explanation of your reasoning.
5. Rate the fit on a scale from 0-10, where:
   - 0 = Very poor fit, sentence does not match the category at all
   - 10 = Perfect fit, sentence matches exactly the category description

# Response Format:
Your response must follow this exact JSON format. The explanation must be a single-line string with no newlines:
```json
{{
  "explanation": "Brief explanation of how well the sentence matches the category and your reasoning for the score",
  "completeness_score": <integer from 0-10>
}}
```

Only include the JSON object in your response, with no additional text before or after.
""" 