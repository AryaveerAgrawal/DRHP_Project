Demo Dataset for respective input and table output:

I created many variations in demo dataset so it gives a better idea for varying inputs.

Input: sh7_2

Output and System Design Diagram: https://drive.google.com/drive/u/0/folders/1VCWjObnjxgK1qvmeOAT3wS-d8bLluhq_

Used ChatGPT/Claude/Gemini for helping to frame structure, but I firstly had brief idea of how to approach the problem. I wanted to use HuggingFace Transformers to do this project, so as to have a proper pipeline and later system design to analyse behind the scenes of extracting data.

Compiled list of prompts:

ChatGPT: Use ChatGPT Deep Research to explain-

Task 1: Build a DRHP Capital Structure Drafting Agent
Your job is to build an AI driven system that:
1. Ingests company filings and compliance documents — documents such as SH-7
(share capital changes), PAS-3 (allotment returns), board resolutions, and so on.
2. Reads and classifies each document — figuring out what type it is, whether it's an
official filing or an unofficial draft, and what corporate event it relates to.
3. Produces a draft capital structure table — the kind you'd see in an actual DRHP,
showing how the company's share capital has evolved over time.
A sample draft Authorised share capital change within capital structure looks like this:
Each row should be traceable to a specific source document (e.g., SH-7, PAS-3, board
resolution). If a field can't be confirmed from the available documents, it should be flagged —
not filled in with a best guess.
Note: Sample input documents for Capital Structure can be found here: Assignment File
Requirement:
1. Understand the problem first by researching what an Authorised share capital
change is and what information it is expected to capture. Ask yourself, how will you
prepare an Authorised share capital change of a company using different documents
discussed above.
2. We have provided you sample PAS-3 and SH-7 data for your reference. Create a
dummy sample dataset consisting of 4 SH-7 documents, with 3 attachment
documents for each SH-7. The purpose is to test how quickly and accurately you can
understand the document structure and the nuances in the content.
3. Your AI system should take 4 SH-7 documents as inputs to generate a draft
Authorised share capital change
4. The resulting Authorised share capital change should track how the company’s share
capital has evolved over time, reflecting each change in share capital based on the
information contained in the documents.


So I found facebook/bart-large-mnli would be appropriate to use here. Then I input the prompt:

ChatGPT: Use the Hugging Face Tranformer facebook/bart-large-mnli so as I am inputing the image in frontend I get proper data extracted using backend. 

But it provided a complex code where OCR was required and used 'pdf2image' by default.

So I later had to make changes so it's approrpirate for markdown files(.md) format and dosen't unncessarily complicate the structure. After fixing I was able to get extracted data from a single uploaded file.

Then I moved on to multiple files in a folder/ work in a batch, as basic structure got more and more clearer. I solved small errors using Claude sometimes GPT sometimes Gemini. Finally for last major hurdle I used GPT/Claude:

ChatGPT: Generate me a demo synthetic datset for 4 different SH-7 documents.

Then,

Claude: Edit my code such that I am able to upload an entire folder. I uploaded my frontend and backend code.

Then it made respective changes in frontend and backend. Still it was giving me output in JSON format not in form of a table.
So I used a different AI.

ChatGPT: Provide me code such that I get extracted JSON information from backend in the form of a structured table. 

So it created CapitalTable.jsx folder.
And finally after final set of changes, I uploaded my demo datset, then got respective different outputs.


