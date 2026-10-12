
## QW-7 Credential End-Caps (2026-10-12, Chris)
- Credentials are tagged to 0s and 1s bytecode - there is never an accidental secret in memory, string, or log.
- Getting to them means getting down to the bare metal: Google-auth-bound identities resolved against the binary itself, stored deep-encrypted at the end-cap layer.
- Threat model in one line: to steal it, you have to be handed it. No possibility of crunching or exploiting - security is total at the end caps.
