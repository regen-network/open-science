# Open Science (draft) [![Join Regen ESP Open Science Discussion Group on Telegram](https://patrolavia.github.io/telegram-badge/chat.png)](https://t.me/joinchat/HsbSJhBNvOhSienO_x6Z1g)
TBD: About the open science group, core terminology

Ecological State Protocols (ESPs) describe protocols for the Regen platform, including core protocol specifications, client APIs, and contract standards.

<!-- A browsable version of all current and draft Indicators can be found on [the official ESP site](tbd). -->
# Indicators (draft)
- https://github.com/regen-network/ind-notill
- https://github.com/regen-network/ind-soc

# Contributing
TBD. Review and adapt contributing guidelines here. 

 1. Review [ESP-0001](ESPS/esp-0001.md).
 2. Fork the repository by clicking "Fork" in the top right.
 3. Add your ESP to your fork of the repository. There is a [template ESP here](esp-XXXX.md).
 4. Submit a Pull Request to Regen Networks's [ESPs repository](https://github.com/regen-network/ESPs).

Your first PR should be a first draft of the final ESP. It must meet the formatting criteria enforced by the build (largely, correct metadata in the header). An editor will manually review the first PR for a new ESP and assign it a number before merging it. Make sure you include a `discussions-to` header with the URL to a discussion forum or open GitHub issue where people can discuss the ESP as a whole.

If your ESP requires images, the image files should be included in a subdirectory of the `assets` folder for that ESP as follows: `assets/esp-X` (for esp **X**). When linking to an image in the ESP, use relative links such as `../assets/esp-X/image.png`.

Once your first PR is merged, we have a bot that helps out by automatically merging PRs to draft ESPs. For this to work, it has to be able to tell that you own the draft being edited. Make sure that the 'author' line of your ESP contains either your Github username or your email address inside <triangular brackets>. If you use your email address, that address must be the one publicly shown on [your GitHub profile](https://github.com/settings/profile).

When you believe your ESP is mature and ready to progress past the draft phase, you should do one of two things:

 - **For a Standards Track ESP of type Core**, ask to have your issue added to [the agenda of an upcoming Regen Open Science meeting](tbd), where it can be discussed for inclusion in a future release. If implementers agree to include it, the ESP editors will update the state of your ESP to 'Accepted'.
 - **For all other ESPs**, open a PR changing the state of your ESP to 'Final'. An editor will review your draft and ask if anyone objects to its being finalised. If the editor decides there is no rough consensus - for instance, because contributors point out significant issues with the ESP - they may close the PR and request that you fix the issues in the draft before trying again.

# ESP Status Terms

* **Draft** - an ESP that is undergoing rapid iteration and changes.
* **Last Call** - an ESP that is done with its initial iteration and ready for review by a wide audience.
* **Accepted** - a core ESP that has been in Last Call for at least 2 weeks and any technical changes that were requested have been addressed by the author. The process for Core Devs to decide whether to encode an ESP into their clients as part of a hard fork is not part of the ESP process. If such a decision is made, the ESP will move to final.
* **Final (non-Core)** - an ESP that has been in Last Call for at least 2 weeks and any technical changes that were requested have been addressed by the author.
* **Final (Core)** - an ESP that the Core Devs have decided to implement and release in the future . 
* **Deferred** - an ESP that is not being considered for immediate adoption. May be reconsidered in the future for a subsequent hard fork.

# Preferred Citation Format

The canonical URL for as ESP that has achieved draft status at any point is at https://tbd.regen.network/. For example, the canonical URL for ESP-0001 is https://tbd.regen.network/ESPS/esp-0001.

# Validation

ESPs must pass some validation tests....

It is possible to run the ESP validator locally:
```
gem install esp_validator
esp_validator <INPUT_FILES>
```

# Automerger

The ESP repository contains an "auto merge" feature to ease the workload for ESP editors.  If a change is made via a PR to a draft ESP, then the authors of the ESP can Github approve the change to have it auto-merged by the [esp-automerger](https://github.com/esp-automerger/automerger) bot.

