# Passive policy baseline: actual results

No permanent blackout fix or physical recovery/prevention is established. These captures read software state only; physical picture state was unobserved. Root access remains host-assisted. No target getters, setters, ioctls, display/power/factory controls, service restarts or firmware changes were performed by these captures.

## Accepted baseline

The actual [174544Z record](pqe-policy-baseline-20261026T174544Z.json), its adjacent intent and driver outputs retain the successful run. Independent review of raw evidence reproduced the saved summary exactly and found no blocking issue. The run used frozen reader SHA256 `161af4bd011cb81f32cf69e8e189ced3b15045c0eaf7df5820120cf2ff99bb07` and tests SHA256 `1199faf2dbb695a9af79474737b4ba71bf64c0bd2785b59824a0e74e35ab977c`, archived under `pqe-policy-reader-reviews/161af4bd011cb81f-1199faf2dbb6/`.

The authenticated root command returned zero without timeout. All 23 sections, 37 exact-length dd groups and 240 requested memory bytes were retained. Both endpoint checks agreed on boot, PID 706, executable, process start tick 603, installed-source hashes, pointers and all 1,345 map lines. Uptime advanced from 58355.79 to 58356.56: 0.77 seconds. Reads were sequential, not atomic; intervening daemon changes are not excluded.

Live bindings identify base RoseMVideoEnhancer, QDDimming and DimmingBackendRoseMQD objects against the exact mapped library. The VideoEnhancer state and separately resolved DLSR shared state alias in this snapshot; that relationship was measured rather than assumed. QDDimming's initialized byte is 1. Its outer header agrees with the guarded inner-state and backend pointers, and the backend virtual target lies in the expected executable mapping.

| Field | Raw value |
| --- | --- |
| DLSR / HDR class | 5 / 1 |
| GSR enable / class | 0 / 0 |
| Object count | 53 |
| Weber gain / target / ramp count | 1023 / 1023 / 0 |
| QDDimming working values | 236 / 236 |
| Backend requested-value cache | 236 |

The GSR enable word was zero and Weber gain/target were at the reconstructed clamp maximum in this snapshot. The working values and backend request cache were nonzero. These are raw software values, not calibrated light measurements. Final-duty branch gates were not all sampled, so the snapshot does not establish which policy contributed to the requested output. It proves neither successful hardware transport/application nor physical light, fault onset or causality.

## Earlier incomplete attempt

The [173952Z record](pqe-policy-baseline-20261026T173952Z.json) is preserved as rejected, with raw transport output, intent and driver outputs. Its root command timed out at the existing 25-second limit before endpoint guards completed. Partial field bytes are not an accepted baseline. The source-backed performance issue was repeated Bash line-by-line mapping scans; fresh map validation was retained using a faster reviewed AWK parser. The timeout was not extended. The corrected reader passed 21 offline tests before the one successful finite run.

The incomplete attempt used separately archived reader revision `8575b16accb3f3b6-5b1698caac0f`. An earlier archived revision `a966e83501294027-94ccef13d3b7` was rejected during offline review and was not run against the TV. The three archives preserve the reviewed stages; they do not represent every intermediate draft.

## Remaining diagnostic gap

The useful next comparison is physically observed visible Apps → sparse Home/Live → sustained blackout, with synchronized policy fields, controller traffic and fault-state samples. This baseline supplies typed field locations and tested read mechanics. An unobserved snapshot cannot provide that transition or establish which operation first causes the physical panel to go dark. Historical 176-file and preceding 43-file evidence snapshots remain unchanged.
