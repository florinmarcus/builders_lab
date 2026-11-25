Read the file {IN}. It holds "prompt" (a fixed instruction) and "items" (questions with ids).

For each item, on its own: take the prompt text exactly as given, with the item's question appended after the final "Question:" line, and do what that combined message asks, as if it were the only message you had ever received. Do not let one item influence another. Do not use any tools other than reading this file and writing the output file. Do not look anything up.

Write the output file {OUT}: one line per item, in item order, each line exactly:
{"id": "<id>", "output": <the JSON object you produced for that item>}
Nothing else in the file. Then reply "done".
