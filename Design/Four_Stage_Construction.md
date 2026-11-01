# Four-stage ordinary building construction

Ordinary catalog buildings use the placed finished visual as their construction source, including future Tripo replacements. No extra partial FBX is needed. Roads retain their authored sequence; lighthouse reconstruction remains unchanged.

- 0–20%: foundation preparation, a temporary base and stacked timber.
- 20–60%: structural construction, bottom-up reveal with temporary scaffolding.
- 60–100%: finishing the main structure; scaffolding removed at 95%, supplies at 85%.
- 100%: complete; original finished model and original materials restored.

The existing schedule duration, simulation-speed provider, progress, completion event and saved progress remain authoritative. The reveal shader clips color, depth and shadow passes. Temporary materials are owned by the construction instance and disposed when construction completes. Failed shader initialization leaves the original model visible.

Validation: create `work/four-stage.request` and refresh Unity while stopped. `Assets/Editor/FourStageConstructionValidation.cs` checks catalog buildings, phase labels, original-model visibility, completion, progress rewind and shader errors. Output: `work/four-stage-validation.txt`, plus four rendered wood-shelter previews. This does not add new worker job scheduling or dismantling mechanics.
