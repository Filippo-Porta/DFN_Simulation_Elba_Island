# DFN_Simulation_Elba_Island

Hi, and welcome to this repository!

Here you can find the code I used for the analysis presented in my submitted article on permeability anisotropy in granitic rocks, imparted by sub-seismic faults in an interacting damage zone (DFN approach, Elba Island case study).

Contents

**`aperture.py`** — Collects and aggregates fracture aperture data from multiple DFNWorks simulation runs into a single cumulative CSV file, for further statistical analysis.

**`backbone.py`** — Extracts and analyzes the conductive backbone of the fracture network: builds the full graph, applies an iterative 2-core filter to remove dead-end fractures, computes the average network degree, and generates a visualization of the 2-core backbone network.

I have also added sensitivity analysis scripts to evaluate how varying key parameters affects the aperture calculation.

The hydraulic aperture b is computed from the aperture-length scaling law:

*b = γ · r^β*

where r is the fracture radius, γ is an empirical scaling factor, and β is the scaling exponent. The sensitivity analysis explores how varying γ and β affects the resulting aperture distribution
