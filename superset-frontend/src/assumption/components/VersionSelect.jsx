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

  let content = null;
  if (fetching) {
    content = <PreLoader />;
  } else if (!fetching && isEmpty(versions)) {
    content = <h4>No versions found. Please upload the table file first</h4>;
  } else if (!fetching && !isEmpty(versions)) {
    content = (
      <FormControl variant="outlined" className={classes.formControl}>
        <Select value={version} onChange={setVersion}>
          <MenuItem value="upload">Upload</MenuItem>
          <MenuItem value="modify">Modify</MenuItem>
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
