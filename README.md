# GenLayer Decentralized Insurance Platform

A decentralized insurance platform where AI validators evaluate claims and decide on payouts through Optimistic Democracy consensus. Built on GenLayer Testnet Bradbury.

---

## What is this

Traditional insurance companies control the entire claims process. They decide what counts as a valid claim, how much to pay, and when. There is no transparency and disputes are resolved by the same party that profits from denying claims.

I built this to explore what a fully transparent insurance process looks like when the claims adjuster is an AI that reads the actual evidence and commits its reasoning onchain. Multiple validators independently evaluate each claim and must agree before any decision is finalized. Nobody can alter the result after the fact.

---

## How it works

A user registers a policy with a type, coverage description, conditions, and coverage amount. The four supported policy types are travel, health, property, and crypto. When a covered event occurs the user files a claim with a description of what happened and a URL pointing to evidence. The contract fetches that URL and an AI adjuster evaluates whether the event matches the coverage, whether the evidence supports the claim, and whether the policy conditions are met. The decision is APPROVED or DENIED with full reasoning stored onchain.

---

## Functions

register_policy takes a policy type, coverage description, conditions, and coverage amount. Policy type must be travel, health, property, or crypto.

file_claim takes a policy id, a description of the event, and a URL pointing to evidence. The policy must be active and have no existing claim.

process_claim takes a policy id and triggers the AI evaluation through Optimistic Democracy. The AI fetches the evidence URL and decides whether to approve or deny the claim.

cancel_policy takes a policy id and cancels an active policy.

get_policy shows the full policy state including type, coverage, status, claim status, decision, and reasoning.

get_platform_summary shows total policies, total claims, and total approved claims.

---

## Test results

Registered a crypto policy covering exchange hacks and smart contract exploits. Filed a claim describing a hack with a Wikipedia article on cryptocurrency crime as evidence. The AI denied the claim because the Wikipedia page was generic and did not confirm any specific hack affecting the claimant. The reasoning was accurate and directly addressed why the evidence did not meet the policy conditions.

---

## How to run it

Go to GenLayer Studio at https://studio.genlayer.com and create a new file called insurance_platform.py. Paste the contract code and set execution mode to Normal Full Consensus. Deploy with your address as owner_address.

Follow this order and wait for FINALIZED at each step. Run get_platform_summary first, then register_policy with your coverage details, then get_policy to confirm it is active, then file_claim with an event description and evidence URL, then process_claim to trigger the AI evaluation, then get_policy to see the final decision.

Note: the contract in this repository uses the Address type in the constructor as required by genvm-lint. When deploying in GenLayer Studio use a version that receives str in the constructor and converts internally with Address(owner_address) since Studio requires primitive types to parse the contract schema correctly.

---

## Resources

GenLayer Docs: https://docs.genlayer.com

Optimistic Democracy: https://docs.genlayer.com/understand-genlayer-protocol/core-operations/optimistic-democracy

Equivalence Principle: https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/optimistic-democracy/equivalence-principle

GenLayer Studio: https://studio.genlayer.com

Discord: https://discord.gg/8Jm4v89VAu
