# Reference Data

## ahmed-front-geo.dat

Original measured front-nose geometry data for the Ahmed body, from S.R. Ahmed (DLR Braunschweig), redistributed via the ERCOFTAC Classic Collection (case082, Becker/Lienhart/Stoots):

http://cfd.mace.manchester.ac.uk/ercoftac/doku.php?id=cases:case082

Format: raw (x, y, z) point coordinates in mm, representing 1/4 of the front nose surface (exploiting vertical and horizontal symmetry). This is a digitized/scanned point cloud (~20,000 points, irregular spacing), not a clean set of cross-sectional curves.

**Not used directly for geometry construction.** Reconstructing a CAD surface from this raw point cloud (binning, curve fitting per station, lofting) was evaluated and found to add substantial implementation complexity and surface-quality risk for a secondary geometric feature — the dominant physics under investigation in this project is rear-slant-angle-driven separation, not nose-profile fidelity. The project instead uses a standard tangent-arc/fillet approximation of the nose (see `geometry/generate_ahmed_body.py`), consistent with the majority of published Ahmed body CFD studies.

This file is retained for reference and as documentation of that decision, and could be used as the basis for a higher-fidelity geometry reconstruction in a future extension if justified.

## ahmed1984_cd_vs_angle.csv
(to be added — Ahmed et al. 1984 experimental C_D vs slant angle, digitized from published plots)

## lienhart_becker_wake.csv
(to be added — Lienhart & Becker 2003 wake velocity data at 25°, digitized from published plots)
