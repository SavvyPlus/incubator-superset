import React, { useEffect } from 'react';
import Button from '@material-ui/core/Button';
import Backdrop from '@material-ui/core/Backdrop';
import CircularProgress from '@material-ui/core/CircularProgress';
import TextField from '@material-ui/core/TextField';
import { makeStyles } from '@material-ui/core/styles';
import MaterialTable from './materialTable';
import DeleteDialog from './DeleteDialog';
import PreLoader from '../../components/PreLoader';

const useStyles = makeStyles(theme => ({
  backdrop: {
    zIndex: theme.zIndex.drawer + 1,
    color: '#fff',
  },
  fetchBtn: {
    marginBottom: 20,
  },
}));

export default function AssumptionTable({
  version,
  table,
  tableData,
  fetchingVersions,
  fetchTableData,
  saveTableData,
}) {
  const classes = useStyles();
  const [openBD, setOpenBD] = React.useState(false);
  const [savingData, setSavingData] = React.useState(false);

  const [note, setNote] = React.useState('');
  const [fetchingData, setFetchingData] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [selctedData, setSelectedData] = React.useState([]);

  useEffect(() => {
    setNote('');
  }, [version, table]);

  const getTableData = td => {
    const columns = [];
    for (let i = 0; i < td.columns.length; i++) {
      columns.push({ title: td.columns[i], field: td.columns[i] });
      // if (td.columns[i] === 'Aggregate_MW' || td.columns[i] === 'Capacity_MW') {
      //   columns.push({
      //     title: td.columns[i],
      //     field: td.columns[i],
      //     type: 'numeric',
      //   });
      // } else {
      //   columns.push({ title: td.columns[i], field: td.columns[i] });
      // }
    }
    const data = td.data;
    return { columns, data };
  };

  const handleNoteChange = event => {
    setNote(event.target.value);
  };

  const handleFetchTableData = () => {
    setFetchingData(true);
    fetchTableData(table, version).then(() => {
      setFetchingData(false);
    });
  };

  const handleSaveData = () => {
    setOpenBD(true);
    setSavingData(true);
    return saveTableData(version).then(() => {
      setSavingData(false);
    });
  };

  const handleDialogClose = () => {
    setOpen(false);
  };

  const tableD = getTableData(tableData);

  return (
    <div className="mb-50">
      <h3 className="mt-50">Step 4: Write Your Note About This Modify</h3>
      <TextField
        required
        fullWidth
        id="upload-note"
        label="Required"
        value={note}
        placeholder="Write your note about this upload file"
        onChange={handleNoteChange}
      />

      <h3 className="mt-50">Step 5: Fetch and Modify</h3>
      <div>
        <Button
          className={classes.fetchBtn}
          disabled={!version || fetchingVersions || note === ''}
          variant="contained"
          color="primary"
          onClick={handleFetchTableData}
        >
          {fetchingVersions || fetchingData ? (
            <div style={{ width: 39.68 }}>
              <PreLoader />
            </div>
          ) : (
            'Fetch'
          )}
        </Button>

        <MaterialTable
          title={table}
          localization={{
            body: {
              emptyDataSourceMessage: fetchingData
                ? 'Fetching...'
                : 'Please fetch table data first',
            },
          }}
          columns={tableD.columns}
          data={tableD.data}
          editable={{
            onRowAdd: newData =>
              new Promise(resolve => {
                setTimeout(() => {
                  // resolve();
                  console.log('adding....');
                }, 600);
              }),
            onRowUpdate: (newData, oldData) => handleSaveData(),
            // new Promise(resolve => {
            //   setTimeout(() => {
            //     resolve();
            //     if (oldData) {
            //       console.log('updating....');
            //     }
            //   }, 600);
            // }),
            onRowDelete: oldData =>
              new Promise(resolve => {
                setTimeout(() => {
                  resolve();
                  console.log('deleting....');
                }, 600);
              }),
          }}
          options={{
            selection: true,
            pageSize: 10,
          }}
          actions={[
            {
              tooltip: 'Remove All Selected Users',
              icon: 'delete',
              onClick: (evt, data) => {
                setOpen(true);
                setSelectedData(data);
              },
            },
          ]}
        />
      </div>
      <DeleteDialog
        open={open}
        data={selctedData}
        handleClose={handleDialogClose}
      />
      <Backdrop className={classes.backdrop} open={openBD}>
        {savingData ? (
          // <CircularProgress color="inherit" />
          <h2>Saving Data...</h2>
        ) : (
          <h2>Success! Reloading Data...</h2>
        )}
      </Backdrop>
    </div>
  );
}
