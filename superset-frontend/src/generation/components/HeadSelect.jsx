import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import ToggleButton from '@material-ui/lab/ToggleButton';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';

const dateRanges = ['1D', '3D', '7D', '30D', '1Y', 'ALL'];
const granularity1 = ['5m', '30m'];
const granularity2 = ['Day', 'Week', 'Month'];
const granularity3 = [
  'Month',
  'Season',
  'Quarter',
  'Half Year',
  'Fin Year',
  'Year',
];

const useStyles = makeStyles(theme => ({
  toggleContainer: {
    margin: theme.spacing(2, 0),
  },
  rangeSelect: {
    marginRight: 20,
  },
  button: {
    backgroundColor: 'white !important',
    color: '#c74523 !important',
  },
  selected: {
    backgroundColor: '#c74523 !important',
    color: 'white !important',
  },
}));

export default function HeadSelect({
  range,
  setRange,
  granularity,
  setGranularity,
}) {
  const handleRange = (event, newRange) => {
    if (newRange !== null) {
      setRange(newRange);
    }

    if (newRange === '3D' || newRange === '7D') {
      setGranularity('30m');
    } else if (newRange === '1Y') {
      setGranularity('Week');
    } else if (newRange === 'ALL') {
      setGranularity('Month');
    }
  };

  const handleGranularity = (event, newGranularity) => {
    setGranularity(newGranularity);
  };

  const classes = useStyles();

  const renderGranularitySelect = () => {
    if (range === '1D') {
      return (
        <ToggleButtonGroup value="5m" exclusive aria-label="granularity">
          <ToggleButton
            classes={{ root: classes.button, selected: classes.selected }}
            value="5m"
            aria-label="5m"
          >
            5m
          </ToggleButton>
        </ToggleButtonGroup>
      );
    } else if (range === '3D' || range === '7D') {
      return (
        <ToggleButtonGroup
          value={granularity}
          exclusive
          aria-label="granularity"
          onChange={handleGranularity}
        >
          {granularity1.map(g => (
            <ToggleButton
              key={g}
              classes={{ root: classes.button, selected: classes.selected }}
              value={g}
              aria-label={g}
            >
              {g}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      );
    } else if (range === '30D') {
      return (
        <ToggleButtonGroup value="Day" exclusive aria-label="granularity">
          <ToggleButton
            classes={{ root: classes.button, selected: classes.selected }}
            value="Day"
            aria-label="Day"
          >
            Day
          </ToggleButton>
        </ToggleButtonGroup>
      );
    } else if (range === '1Y') {
      return (
        <ToggleButtonGroup
          value={granularity}
          exclusive
          aria-label="granularity"
          onChange={handleGranularity}
        >
          {granularity2.map(g => (
            <ToggleButton
              classes={{ root: classes.button, selected: classes.selected }}
              value={g}
              aria-label={g}
            >
              {g}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      );
    }
    return (
      <ToggleButtonGroup
        value={granularity}
        exclusive
        aria-label="granularity"
        onChange={handleGranularity}
      >
        {granularity3.map(g => (
          <ToggleButton
            classes={{ root: classes.button, selected: classes.selected }}
            value={g}
            aria-label={g}
          >
            {g}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
    );
  };

  return (
    <div className={classes.toggleContainer}>
      <ToggleButtonGroup
        className={classes.rangeSelect}
        value={range}
        exclusive
        onChange={handleRange}
        aria-label="Date range"
      >
        {dateRanges.map(dateRange => (
          <ToggleButton
            key={dateRange}
            classes={{ root: classes.button, selected: classes.selected }}
            value={dateRange}
            aria-label={dateRange}
          >
            {dateRange}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
      {renderGranularitySelect()}
    </div>
  );
}
