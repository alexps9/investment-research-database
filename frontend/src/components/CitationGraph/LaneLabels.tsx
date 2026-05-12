import {
  LANE_H,
  LANE_IDS,
  LANE_LABEL_W,
  LANES,
  SUB_LANE_H,
  SUB_LANES,
} from '@/lib/citation-graph/constants'
import { LANES_BAND_H } from '@/lib/citation-graph/layout'
import styles from './CitationGraph.module.css'

export function LaneLabels() {
  return (
    <>
      {/* Lane title column */}
      <div
        className={styles.laneLabels}
        style={{ width: LANE_LABEL_W, height: LANES_BAND_H }}
      >
        {LANE_IDS.map((laneId, idx) => {
          const lane = LANES[laneId]
          return (
            <div
              key={laneId}
              className={
                idx === LANE_IDS.length - 1
                  ? `${styles.laneLabel} ${styles.laneLabelLast}`
                  : styles.laneLabel
              }
              style={{ height: LANE_H }}
            >
              <div className={styles.laneLabelTitle}>
                L{laneId}. {lane.title}
              </div>
              <div className={styles.laneLabelQuestion}>{lane.question}</div>
            </div>
          )
        })}
      </div>
      {/* Sub-lane captions — stacked over the lane labels */}
      <div
        className={styles.subLaneLabels}
        style={{ width: LANE_LABEL_W, height: LANES_BAND_H }}
      >
        {LANE_IDS.map((laneId, laneIdx) =>
          SUB_LANES.map((subId, subIdx) => {
            const sub = LANES[laneId].subLanes[subId]
            const top = laneIdx * LANE_H + subIdx * SUB_LANE_H
            return (
              <div
                key={`${laneId}-${subId}`}
                className={styles.subLaneLabel}
                style={{
                  position: 'absolute',
                  top,
                  width: LANE_LABEL_W,
                  height: SUB_LANE_H,
                  // Push the caption into the track area only on hover-less default
                  // so sub-lane text reads alongside its main lane title.
                  paddingLeft: 14,
                  opacity: 0, // hidden: main lane label carries the info; sub-lanes are visually coded by position
                }}
                aria-hidden
              >
                {laneId}-{subId}. {sub.title}
              </div>
            )
          }),
        )}
      </div>
    </>
  )
}
