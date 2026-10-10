# Pass the Baton

**What applies to the people should apply to those who lead them.**

*Nederlands: [Het Stokje Doorgeven](translations/nl/README.md)*

All over the world, people hand their work over to the next generation at a certain age. This movement asks leaders to do the same: anyone who has reached the statutory retirement age of their own country, and at the latest 67, does not start a new term in one of the highest offices.

Not out of distrust of older people, but out of respect for renewal.

## What's here

| File | Contents |
| --- | --- |
| [MANIFESTO.md](MANIFESTO.md) | The manifesto: the problem, the demand, our principles and answers to objections |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How a small team of AI agents supports the campaign, with a human approving everything that goes out |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to build, translate or start a local chapter |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | How we treat each other |
| [translations/](translations/) | The texts in other languages (Dutch for now) |

## Status

The project is just starting. What exists today: the manifesto and the architecture. Next, in this order:

1. **Identity and website**: a branding agent builds the brand (tone of voice, colours, typography, logo proposals, the "why" in short texts); a simple website carries the manifesto.
2. **Facts and languages**: research and localisation agents; country profiles and the manifesto in the first languages.
3. **Reach**: partner and media agents, always with prior human approval.
4. **Scale**: volunteer agent, coordinator, local chapters and the digital baton.
5. **Second line**: extending the demand to other political offices.

Still open: a figurehead. Athletes carrying the baton would be a strong image.

## How the agents run

The agents live in [`agents/`](agents/) and run on GitHub Actions. Every agent delivers its work as a **pull request**. Merging a pull request is the human approval: nothing an agent makes goes live until a maintainer has reviewed and merged it.

## Principles

Non-violent, independent of any party, transparent. No fake accounts, no unsolicited mass messaging, and everything that goes out in the movement's name is approved by a human first. See [Limits and safeguards](docs/ARCHITECTURE.md#limits-and-safeguards).

## Licence

- **Code**: [GNU Affero General Public License v3.0](LICENSE). Modified versions, including ones run as a web service, stay open.
- **Texts** (manifesto, documentation): [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Free to share and translate, with attribution and under the same licence.
