---
eip: 1
title: ESP Purpose and Guidelines
status: Active
type: Meta
author: Daniel Swid <daniel@regen.network>
        https://github.com/regen-network/ESPs/blob/master/esp/template-0000.md
created: 2019-07-08
updated: na
---

## What is an ESP?

ESP stands for Ecological State Protocol. An ESP is a design document providing information to the Regen Network community, or describing a new protocol for Regen Network. The ESP should provide a concise technical specification of the protocol. The ESP author is responsible for building consensus within the community and documenting dissenting opinions.

## ESP Rationale

## ESP Types

There are three types of EP:

- **Type 1** - example
- **Type 2** - example  
- **Type 1** - example  

It is highly recommended that a single ESP contain a single key proposal or new idea. The more focused the ESP and geographically context specific, the more successful it tends to be. 

An ESP must meet certain minimum criteria. It must be a clear and complete description of the proposed protocol....

### Special requirements for Core ESPs

## ESP Work Flow

Parties involved in the process are you, the champion or *ESP author*, the [*ESP editors*](#esp-editors), and the [*Regen Network Core Developers*](https://github.com/orgs/regen-network/teams/dev-team).

:warning: Before you begin, vet your idea, this will save you time. Ask the Regen community first if an idea is original to avoid wasting time on something (searching the Internet does not always do the trick).

Your role as the champion is to write the ESP using the style and format described below, shepherd the discussions in the appropriate forums, and build community consensus around the idea. Following is the process that a successful ESP will move along:

```
[ WIP ] -> [ DRAFT ] -> [ LAST CALL ] -> [ ACCEPTED ] -> [ FINAL ]
```

Each status change is requested by the ESP author and reviewed by the ESP editors. Use a pull request to update the status. Please include a link to where people should continue discussing your ESP. The ESP editors will process these requests as per the conditions below.

* **Active** -- Some Informational and Process ESPs may also have a status of “Active” if they are never meant to be completed. E.g. ESP 0000 (this ESP).
* **Work in progress (WIP)** -- Once the champion has asked the Ethereum community whether an idea has any chance of support, they will write a draft EWAP as a [pull request]. Consider including an implementation \if this will aid people in studying the ESP.
  * :arrow_right: Draft -- If agreeable, ESP editor will assign the ESP a number (generally the issue or PR number related to the ESP) and merge your pull request. The ESP editor will not unreasonably deny an ESP.
  * :x: Draft -- Reasons for denying draft status include being too unfocused, too broad, duplication of effort, being technically unsound, not providing proper motivation or addressing backwards compatibility, or not in keeping with the [Ethereum philosophy](https://github.com/ethereum/wiki/wiki/White-Paper#philosophy).
* **Draft** -- Once the first draft has been merged, you may submit follow-up pull requests with further changes to your draft until such point as you believe the ESP to be mature and ready to proceed to the next status. An ESP in draft status must be implemented to be considered for promotion to the next status (ignore this requirement for core ESPs).
  * :arrow_right: Last Call -- If agreeable, the ESP editor will assign Last Call status and set a review end date (`review-period-end`), normally 14 days later.
  * :x: Last Call -- A request for Last Call status will be denied if material changes are still expected to be made to the draft. We hope that ESPs only enter Last Call once, so as to avoid unnecessary noise on the RSS feed.
* **Last Call** -- This ESP will listed prominently on the [TBD](https://esps.regen.network/) website (subscribe via RSS at [tbd.xml](/tbd.xml)).
  * :x: -- A Last Call which results in material changes or substantial unaddressed technical complaints will cause the ESP to revert to Draft.
  * :arrow_right: Accepted (Core ESPs only) -- A successful Last Call without material changes or unaddressed technical complaints will become Accepted.
  * :arrow_right: Final (Not core ESPs) -- A successful Last Call without material changes or unaddressed technical complaints will become Final.
* **Accepted (Core ESPs only)** -- This ESP is in the hands of the Regen Network client developers. Their process for deciding whether to encode it into the Regen Ledger .
  * :arrow_right: Final -- Standards Track Core ESPs must be implemented in at least three viable Regen Network clients before it can be considered Final. When the implementation is complete and adopted by the community, the status will be changed to “Final”.
* **Final** -- This ESP represents the current state-of-the-art. A Final ESP should only be updated to correct errata.

Other exceptional statuses include:

* **Deferred** -- This is for core ESPs that have been put off for a future hard fork.
* **Abandoned** -- This ESP is no longer pursued by the original authors or it may not be a (technically) preferred option anymore.
* **Rejected** -- An ESP that is fundamentally broken or a Core ESP that was rejected by the Core Devs and will not be implemented.
* **Active** -- This is similar to Final, but denotes an ESP which may be updated without changing its ESP number.
* **Superseded** -- An ESP which was previously final but is no longer considered state-of-the-art. Another ESP will be in Final status and reference the Superseded ESP.

## What belongs in a successful ESP?

Each ESP should have the following parts:

- Preamble - RFC 822 style headers containing metadata about the ESP, including the ESP number, a short descriptive title (limited to a maximum of 44 characters), and the author details. See [below](https://github.com/regen-network/ESPs/blob/master/ESPS/esp-1.md#eip-header-preamble) for details.
- Simple Summary - “If you can’t explain it simply, you don’t understand it well enough.” Provide a simplified and layman-accessible explanation of the ESP.
- Abstract - a short (~200 word) description of the technical issue being addressed.
- Motivation (*optional) - The motivation is critical for ESPs that want to change an exisiting Regen protocol. It should clearly explain why the existing protocol specification is inadequate to address the problem that the ESP solves. ESP submissions without sufficient motivation may be rejected outright.
- Specification - The technical specification should describe the syntax and semantics of any new feature. The specification should be detailed enough to allow competing, interoperable implementations for any of the current Regen Network platforms [TBD](https://github.com/regen-network/wiki/wiki/Clients).
- Rationale - The rationale fleshes out the specification by describing what motivated the design and why particular design decisions were made. It should describe alternate designs that were considered and related work, e.g. how the feature is supported in other languages. The rationale may also provide evidence of consensus within the community, and should discuss important objections or concerns raised during discussion.
- Backwards Compatibility - All ESPs that introduce backwards incompatibilities must include a section describing these incompatibilities and their severity. The ESP must explain how the author proposes to deal with these incompatibilities. ESP submissions without a sufficient backwards compatibility treatise may be rejected outright.
- Test Cases - Test cases for an implementation are mandatory for ESPs that are affecting consensus changes. Other ESPs can choose to include links to test cases if applicable.
- Implementations - The implementations must be completed before any ESP is given status “Final”, but it need not be completed before the ESP is merged as draft. While there is merit to the approach of reaching consensus on the specification and rationale before writing code, the principle of “rough consensus and running code” is still useful when it comes to resolving many discussions of API details.
- Copyright Waiver - All ESPs must be in the public domain. See the bottom of this ESP for an example copyright waiver.

## ESP Formats and Templates

ESPs should be written in [markdown] format.
Image files should be included in a subdirectory of the `assets` folder for that ESP as follows: `assets/esp-X` (for esp **X**). When linking to an image in the ESP, use relative links such as `../assets/esp-X/image.png`.

## EIP Header Preamble

Each EIP must begin with an [RFC 822](https://www.ietf.org/rfc/rfc822.txt) style header preamble, preceded and followed by three hyphens (`---`). This header is also termed ["front matter" by Jekyll](https://jekyllrb.com/docs/front-matter/). The headers must appear in the following order. Headers marked with "*" are optional and are described below. All other headers are required.

` esp:` <ESP number> (this is determined by the ESP editor)

` title:` <ESP title>

` author:` <a list of the author's or authors' name(s) and/or username(s), or name(s) and email(s). Details are below.>

` * discussions-to:` \<a url pointing to the official discussion thread\>

` status:` <Draft | Last Call | Accepted | Final | Active | Abandoned | Deferred | Rejected | Superseded>

`* review-period-end:` <date review period ends>

` type:` <Standards Track (Core, Networking, Interface, ERC)  | Informational | Meta>

` * category:` <Core | Networking | Interface | ERC>

` created:` <date created on>

` * updated:` <comma separated list of dates>

` * requires:` <ESP number(s)>

` * replaces:` <ESP number(s)>

` * superseded-by:` <ESP number(s)>

` * resolution:` \<a url pointing to the resolution of this ESP\>

Headers that permit lists must separate elements with commas.

Headers requiring dates will always do so in the format of ISO 8601 (yyyy-mm-dd).

#### `author` header

The `author` header optionally lists the names, email addresses or usernames of the authors/owners of the ESP. Those who prefer anonymity may use a username only, or a first name and a username. The format of the author header value must be:

> Random J. User &lt;address@dom.ain&gt;

or

> Random J. User (@username)

if the email address or GitHub username is included, and

> Random J. User

if the email address is not given.

#### `resolution` header

The `resolution` header is required for Standards Track EIPs only. It contains a URL that should point to an email message or other web resource where the pronouncement about the EIP is made.

#### `discussions-to` header

While an ESP is a draft, a `discussions-to` header will indicate the mailing list or URL where the ESP is being discussed. As mentioned above, examples for places to discuss your ESP include [Regen topics on Telegram](tbd), an issue in this repo or in a fork of this repo.

No `discussions-to` header is necessary if the ESP is being discussed privately with the author.

As a single exception, `discussions-to` cannot point to GitHub pull requests.

#### `type` header

The `type` header specifies the type of ESP: Standards Track, Meta, or Informational. If the track is Standards please include the subcategory (core, networking, interface, or ERC).

#### `category` header

The `category` header specifies the ESP's category. This is required for standards-track ESPs only.

#### `created` header

The `created` header records the date that the ESP was assigned a number. Both headers should be in yyyy-mm-dd format, e.g. 2001-08-14.

#### `updated` header

The `updated` header records the date(s) when the ESP was updated with "substantial" changes. This header is only valid for ESPs of Draft and Active status.

#### `requires` header

ESPs may have a `requires` header, indicating the ESP numbers that this ESP depends on.

#### `superseded-by` and `replaces` headers

ESPs may also have a `superseded-by` header indicating that an ESP has been rendered obsolete by a later document; the value is the number of the ESP that replaces the current document. The newer ESP must have a `replaces` header containing the number of the ESP that it rendered obsolete.

## Auxiliary Files

ESPs may include auxiliary files such as diagrams. Such files must be named ESP-XXXX-Y.ext, where “XXXX” is the ESP number, “Y” is a serial number (starting at 1), and “ext” is replaced by the actual file extension (e.g. “png”).

## Transferring ESP Ownership

It occasionally becomes necessary to transfer ownership of ESPs to a new champion. In general, we'd like to retain the original author as a co-author of the transferred ESP, but that's really up to the original author. A good reason to transfer ownership is because the original author no longer has the time or interest in updating it or following through with the ESP process, or has fallen off the face of the 'net (i.e. is unreachable or isn't responding to email). A bad reason to transfer ownership is because you don't agree with the direction of the ESP. We try to build consensus around an ESP, but if that's not possible, you can always submit a different ESP.

If you are interested in assuming ownership of an ESP, send a message asking to take over, addressed to both the original author and the ESP editor. If the original author doesn't respond to email in a timely manner, the ESP editor will make a unilateral decision (it's not like such decisions can't be reversed :)).

## ESP Editors

The current ESP editors are

` * Daniel Swid (@swidnikk)`

## ESP Editor Responsibilities

For each new ESP that comes in, an editor does the following:

- Read the ESP to check if it is ready: sound and complete. The ideas must make technical sense, even if they don't seem likely to get to final status.
- The title should accurately describe the content.
- Check the ESP for language (spelling, grammar, sentence structure, etc.), markup (Github flavored Markdown), code style

If the ESP isn't ready, the editor will send it back to the author for revision, with specific instructions.

Once the ESP is ready for the repository, the ESP editor will:

- Assign an ESP number (generally the PR number or, if preferred by the author, the Issue # if there was discussion in the Issues section of this repository about this ESP)

- Merge the corresponding pull request

- Send a message back to the ESP author with the next step.

Many ESPs are written and maintained by developers with write access to the Regen codebase. The ESP editors monitor ESP changes, and correct any structure, grammar, spelling, or markup mistakes we see.

The editors don't pass judgment on ESPs. We merely do the administrative & editorial part.

## History

This document was derived heavily from [Ethereums's ESP-1]. Please direct all comments to Regen's ESP editors.

See [the revision history for further details](https://github.com/regen-network/ESPs/commits/master/ESPS/esp-0001.md), which is also available by clicking on the History button in the top right of the ESP.

### Bibliography

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
