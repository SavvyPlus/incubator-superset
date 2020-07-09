import React, { useEffect } from 'react';
import { isEmpty } from 'lodash';
import { makeStyles } from '@material-ui/core/styles';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';
import PreLoader from '../../components/PreLoader';

const useStyles = makeStyles(theme => ({
  formControl: {
    minWidth: 120,
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

export default function VersionSelect({
  versions,
  upsert,
  table,
  version,
  fetching,
  setVersion,
  fetchTableVersions,
}) {
  const classes = useStyles();

  useEffect(() => {
    if (upsert === 'modify') {
      fetchTableVersions(table);
    }
  }, [table]);

  const handleChange = e => {
    setVersion(e.target.value);
  };

  let content = null;
  if (fetching) {
    content = <PreLoader />;
  } else if (!fetching && versions.length === 0) {
    content = (
      <h4>{`No versions found in table ${table}. Please upload the table file first`}</h4>
    );
  } else if (!fetching && versions.length > 0) {
    content = (
      <FormControl variant="outlined" className={classes.formControl}>
        <Select value={version} onChange={handleChange}>
          {versions.map(v => (
            <MenuItem key={v.version} value={v.version}>
              {v.note}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    );
  }

  return (
    <>
      <h3 className="mt-50">Step 3: Select Version</h3>
      {content}
    </>
  );
}
