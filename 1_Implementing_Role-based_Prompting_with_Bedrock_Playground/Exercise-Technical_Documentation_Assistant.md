An internal engineering team at a fictional SaaS company writes fast, informal implementation notes during feature development. Other engineers struggle to make sense of those notes weeks later. The team needs an assistant that turns rough notes into clean, structured internal documentation.

Build a Bedrock Playground prompt that produces this transformation reliably for any set of engineering notes pasted in.

What you need to build
A prompt with a role that frames the assistant as an experienced technical writer for an engineering audience.
An explicit output format that removes ambiguity about structure (sections, headings, bullet lists).
Constraints that prevent the model from inventing implementation details or padding the output beyond a stated length.
Resources provided
A sample set of engineering notes (a Redis caching change with context, behaviors, tradeoffs, and open items) included in the exercise README in the Github Repository: https://github.com/udacity/aws-c1-prompting-llm-reasoning-nd905-cd14762-exercises/tree/main/lesson-1-role-based-prompting/exercises/concept1-role-based-prompting/starter(opens in a new tab).
The Amazon Bedrock Playground in the AWS console with Amazon Nova Pro available as the model.
AWS documentation: the Amazon Bedrock Playground(opens in a new tab) user guide and the playground reference(opens in a new tab).


Test prompt
Run your final prompt against the provided notes and confirm the output:

Reflects every item present in the notes (no fabricated details, no dropped items).
Uses a consistent, scannable structure (section headings or bullet lists).
Stays within the length limit you set.
Optionally, repeat the run at temperature 0 and 0.7 and compare the variation.

Deliverables
The final system prompt or user prompt you wrote.
The model and parameter settings used (model ID, temperature, top-p).
The generated documentation for the provided engineering notes.
Hints
The role is doing most of the work. Be specific about who the writer is, who the reader is, and what the output should look like.
A short list of "do not do this" instructions (no fabricated details, no marketing language, no skipped items) often produces a bigger improvement than a longer list of positive instructions.
How to Access Bedrock Playground
Access the Amazon Bedrock Playground using the AWS Account provided by Udacity.

Click on the Cloud Resources button next to lesson resources button at the bottom of the classroom side panel on the left ( where you see the course progression and lessons ).
Once you're on the cloud resources page, click "Start cloud resource."
Then, once the "Open cloud resource" button is active, click it to open the provided AWS cloud console.
Once there search for Bedrock and select Amazon Bedrock.
Once on the Amazon Bedrock console page, you should see "Playground" under "Test" in the left side panel
Note that you should open the cloud resource when you are currently signed out of your own personal AWS account in case you have one.