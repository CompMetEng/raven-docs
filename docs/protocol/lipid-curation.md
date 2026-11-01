# Curation of lipid reactions

After the biomass composition is adjusted, the reactions that are known to differ in the target organism are curated. The SLIME formalism (Split Lipids Into Measurable Entities) describes lipid metabolism, and it requires curated lipid reactions that match the lipids in the biomass reaction.

:::{admonition} Order of curation and gap-filling
:class: note

Curation can also follow gap-filling. Curated lipid reactions change the gap-filling result, so the protocol curates first.
:::

## The SLIME formalism

SLIME captures the flexibility of lipid metabolism and accepts measurements of lipid classes and of acyl chains. Each lipid species in the biomass composition is split into pseudometabolites for its backbone and its acyl chains, and these are gathered into the measured entities:

```text
phosphatidylcholine (1–16:0, 2–18:0) → phosphatidylcholine backbone
                                       + C16:0 chain + C18:0 chain
phosphatidylcholine backbone + triglyceride backbone + … → lipid backbone
C16:0 chain + C18:0 chain + C18:1 chain + …             → lipid chain
lipid backbone + lipid chain                            → lipid
```

## Applying the template reactions

The `data/reconstruction/` folder of the repository provides template reactions. The protocol reads the templates and applies them with `addLipidReactions` and `addSLIMEreactions`. In outline, the calls add the lipid and transport reactions and the SLIME split reactions:

```matlab
model = addLipidReactions(template, model, modelSce);   % lipid + transport reactions
model = addSLIMEreactions(template, model, modelSce);   % SLIME split reactions
```

The full script reads three template files (`lipidTemplates.txt`, `lipidTransport.txt` and `SLIMERtemplates.txt`) and reorganises them into a `template` structure. It first removes the pre-existing matching reactions and `SLIME rxn` reactions, and the curated set replaces them. Only a subset of the possible acyl-chain distributions is included, to reduce complexity.

## Scaling the acyl chains

After gap-filling, the provided levels of acyl chains and lipid classes turn out to be incompatible, and one of the two must be scaled for a functional model. The protocol assumes that the lipid-class measurements are technically more reliable, and it scales the acyl-chain data:

```matlab
model = scaleLipids(model, 'tails');
```

After the scaling, the model has the lipid reactions that support a flux towards lipid biosynthesis.

The next page is [Gap-filling](gap-filling.md).
