# Third-party components and licences

**No donor source files were copied** into LowHangingFruitMe. The source and data adapters were written as project-specific integrations.

- Frictionless (optional CSV validation library) – https://github.com/frictionlessdata/frictionless-py – MIT, see project licence. Actual runtime dependencies and resolved versions must be recorded in a release SBOM.
- Docling (optional PDF extraction library) – https://github.com/docling-project/docling – MIT source code; model licences and transitive packages require separate review. A Docling-model download is not a reproducible, private-only operation without deployment controls.
- Python standard library; setuptools packaging.

Research-only donors: RapidFuzz, invoice2data, official weclapp SDK, Odoo/Frappe/Dolibarr connector architectures. No runtime incorporation of their code at this stage. See docs/DONORS.md for details.

**Project licence:** A public repository is not automatically an open-source grant. No distribution licence for LowHangingFruitMe has yet been chosen by the owner; select one before distributing packages or accepting third-party code contributions.
