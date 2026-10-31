# Curation of lipid reactions

After adjusting the biomass composition, it is useful to curate reactions already known to differ in the target organism. Using the **SLIME** formalism (Split Lipids Into Measurable Entities) to describe lipid metabolism requires curating the lipid reactions to match the lipids in the biomass reaction.

:::{admonition} Order of curation and gap-filling
:class: note

This step can also be done after gap-filling, but the curation may influence the gap-filling result, so it is done first here.
:::

## The SLIME formalism

SLIME captures the flexibility of lipid metabolism while allowing the user to incorporate measurements of lipid classes and acyl chains. Each lipid species in the biomass composition is split into pseudometabolites for its backbone and acyl chains, which are then gathered into the measured entities:

```text
phosphatidylcholine (1–16:0, 2–18:0) → phosphatidylcholine backbone
                                       + C16:0 chain + C18:0 chain
phosphatidylcholine backbone + triglyceride backbone + … → lipid backbone
C16:0 chain + C18:0 chain + C18:1 chain + …             → lipid chain
lipid backbone + lipid chain                            → lipid
```

## Applying the template reactions

Template reactions are provided in the repository's `data/reconstruction/` folder. The protocol reads these templates and applies them with `addLipidReactions` and `addSLIMEreactions`. In outline, the calls add the lipid and transport reactions and the SLIME split reactions:

```matlab
model = addLipidReactions(template, model, modelSce);   % lipid + transport reactions
model = addSLIMEreactions(template, model, modelSce);   % SLIME split reactions
```

In the full script, three template files are read (`lipidTemplates.txt`, `lipidTransport.txt`, `SLIMERtemplates.txt`), reorganised into a `template` structure, and any pre-existing matching or `SLIME rxn` reactions are removed first so the curated set replaces them. To reduce complexity, only a subset of possible acyl-chain distributions is included.

## Scaling the acyl chains

After gap-filling (next section) it becomes apparent that the provided acyl-chain and lipid-class levels are not fully compatible; one of the two must be scaled for a functional model. Assuming the lipid-class measurements are technically more reliable, the acyl-chain data is scaled:

```matlab
model = scaleLipids(model, 'tails');
```

After scaling, the model has the lipid reactions needed to support a flux toward lipid biosynthesis.

Next: [Gap-filling](gap-filling.md).
