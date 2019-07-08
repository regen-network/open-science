---
eip: <to be assigned>
title: <ESP title>
author: <a list of the author's or authors' name(s) and/or username(s), or name(s) and email(s), e.g. (use with the parentheses or triangular brackets): FirstName LastName (@GitHubUsername), FirstName LastName <foo@bar.com>, FirstName (@GitHubUsername) and GitHubUsername (@GitHubUsername)>
discussions-to: <URL>
status: Draft
type: <Standards Track (a, b, c, d...)  | Meta | Informational>
category (*only required for Standard Track): <Core | Networking | Interface | ERC>
created: <date created on, in ISO 8601 (yyyy-mm-dd) format>
requires (*optional): <ESP number(s)>
replaces (*optional): <ESP number(s)>
---

This is the suggested template for new ESPs.

Note that an ESP number will be assigned by an editor. When opening a pull request to submit your ESP, please use an abbreviated title in the filename, `esp-draft_title_abbrev.md`.

The title should be 44 characters or less.

## Simple Summary
If you can't explain it simply, you don't understand it well enough." Provide a simplified and layman-accessible explanation of the ESP.

## Abstract
A short (~200 word) description of the technical issue being addressed.

## Motivation
<!--The motivation is critical for ESPs that want to change Regen Network core protocols. It should clearly explain why the existing protocol specification is inadequate to address the problem that the ESP solves. ESP submissions without sufficient motivation may be rejected outright.-->
The motivation is critical for ESPs that want to change the Ethereum protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the ESP solves. ESP submissions without sufficient motivation may be rejected outright.

## Specification
The technical specification should describe the syntax and semantics of any new protocol. The specification should be detailed enough to allow competing, interoperable implementations for any of the [Regen Platforms](https://github.com/regen-network/tbd)).

## Rationale
The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.

## Backwards Compatibility
All ESPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The ESP must explain how the author proposes to deal with these incompatibilities. ESP submissions without a sufficient backwards compatibility treatise may be rejected outright.

## Test Cases
Test cases for an implementation are mandatory for ESPs that are affecting consensus changes. Other ESPs can choose to include links to test cases if applicable.

## Implementation
The implementations must be completed before any ESP is given status "Final", but it need not be completed before the ESP is accepted. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of "rough consensus and running code" is still useful when it comes to resolving many discussions of API details.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
