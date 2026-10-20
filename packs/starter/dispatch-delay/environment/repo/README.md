# Dispatch desk
The CLI exposes one summary per parcel group. `domain.py` holds the state vocabulary;
selection, presentation and grouping are separate modules. Dates are calendar strings,
not timestamps. There is no database or clock dependency.
