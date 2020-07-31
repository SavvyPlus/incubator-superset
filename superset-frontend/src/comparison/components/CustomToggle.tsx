/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import ToggleButton from '@material-ui/lab/ToggleButton';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';

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

interface CustomToggleProps {
  name: string;
  value: string;
  setValue: (value: string) => void;
  values: string[];
}

export default function CustomToggle({
  name,
  value,
  setValue,
  values,
}: CustomToggleProps) {
  const handleChange = (
    event: React.MouseEvent<HTMLElement>,
    newVal: string | null,
  ) => {
    if (newVal !== null) {
      setValue(newVal);
    }
  };
  const classes = useStyles();

  return (
    <div className={classes.toggleContainer}>
      <ToggleButtonGroup
        id={name}
        className={classes.rangeSelect}
        value={value}
        exclusive
        onChange={handleChange}
        aria-label={name}
      >
        {values.map(v => (
          <ToggleButton
            key={v}
            classes={{ root: classes.button, selected: classes.selected }}
            value={v}
            aria-label={v}
          >
            {v}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
    </div>
  );
}
