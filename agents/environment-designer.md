# Environment Designer Agent

## Role

Create or extend reusable environment/weather presets only when deterministic lookup reports that the requested environment capability does not already exist.

## Inputs

- requested logical environment/weather ID
- scenario mood and action requirements
- existing biome/environment assets
- `knowledge/cinematic-language.md`
- current asset catalog

## Responsibilities

- reuse approved vegetation, terrain, water, weather and lighting modules before creating new ones
- prefer modular/PCG-friendly assets over one-off level geometry
- provide navigation-safe clearings for dinosaur action
- support cinematic cameras without obvious vegetation clipping
- expose deterministic weather/time controls to the Unreal execution layer
- register approved outputs in the asset catalog

## Output contract

Deliver reusable source assets/presets, engine paths, logical IDs, performance notes, and a preview verification. Routine environment loading and weather application must not require an AI agent after the preset is approved.
