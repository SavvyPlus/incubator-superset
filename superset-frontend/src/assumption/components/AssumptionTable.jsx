import React, { useState, useEffect } from 'react';
import Button from '@material-ui/core/Button';
import Backdrop from '@material-ui/core/Backdrop';
import CircularProgress from '@material-ui/core/CircularProgress';
import TextField from '@material-ui/core/TextField';
import { makeStyles } from '@material-ui/core/styles';
import MaterialTable from './materialTable';
import SaveDialog from './SaveDialog';
import DeleteDialog from './DeleteDialog';
import PreLoader from '../../components/PreLoader';

const useStyles = makeStyles(theme => ({
  backdrop: {
    zIndex: theme.zIndex.drawer + 1,
    color: '#fff',
  },
  fetchBtn: {
    marginBottom: 20,
    minWidth: 80,
  },
  saveBtn: {
    float: 'right',
    minWidth: 80,
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
  const [openBD, setOpenBD] = useState(false);

  const [columns, setColumns] = useState([]);
  const [data, setData] = useState([]);
  const [isModified, setIsModified] = useState(false);

  const [fetchingData, setFetchingData] = useState(false);
  const [openDelete, setOpenDelete] = useState(false);
  const [selectedData, setSelectedData] = useState([]);
  const [openSave, setOpenSave] = useState(false);

  const getTableData = td => {
    const cols = [];
    for (let i = 0; i < td.columns.length; i++) {
      cols.push({ title: td.columns[i], field: td.columns[i] });
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
    const dt = td.data;
    return { cols, dt };
  };

  useEffect(() => {
    const tableD = getTableData(tableData);
    setColumns([...tableD.cols]);
    setData([...tableD.dt]);
  }, [tableData]);

  const handleFetchTableData = () => {
    setFetchingData(true);
    fetchTableData(table, version).then(() => {
      setFetchingData(false);
    });
  };

  const handleDeleteClose = () => {
    setOpenDelete(false);
  };

  const handleSaveOpen = () => {
    setOpenSave(true);
  };

  const handleSaveClose = () => {
    setOpenSave(false);
  };

  const handleDeleteSelected = () => {
    let newData = [...data];
    selectedData.forEach(sd => {
      newData = newData.filter(nd => nd.tableData.id !== sd.tableData.id);
    });
    setData(newData);
    setOpenDelete(false);
    setIsModified(true);
  };

  return (
    <div className="mb-50">
      <h3 className="mt-50">Step 4: Fetch and Modify</h3>
      <div>
        <div>
          <Button
            className={classes.fetchBtn}
            disabled={!version || fetchingVersions}
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

          <Button
            className={classes.saveBtn}
            disabled={!isModified}
            variant="contained"
            color="primary"
            onClick={handleSaveOpen}
          >
            Save
          </Button>
        </div>

        <MaterialTable
          title={table}
          localization={{
            body: {
              emptyDataSourceMessage: fetchingData
                ? 'Fetching...'
                : 'Please fetch table data first',
            },
          }}
          columns={columns}
          data={data}
          editable={
            columns.length > 0
              ? {
                  onRowAdd: newData =>
                    new Promise((resolve, reject) => {
                      setTimeout(() => {
                        setIsModified(true);
                        setData([...data, newData]);

                        resolve();
                      }, 500);
                    }),
                  onRowUpdate: (newData, oldData) =>
                    new Promise((resolve, reject) => {
                      setTimeout(() => {
                        setIsModified(true);

                        const dataUpdate = [...data];
                        const index = oldData.tableData.id;
                        dataUpdate[index] = newData;
                        setData([...dataUpdate]);

                        resolve();
                      }, 500);
                    }),
                  onRowDelete: oldData =>
                    new Promise((resolve, reject) => {
                      setTimeout(() => {
                        setIsModified(true);

                        const dataDelete = [...data];
                        const index = oldData.tableData.id;
                        dataDelete.splice(index, 1);
                        setData([...dataDelete]);

                        resolve();
                      }, 500);
                    }),
                }
              : null
          }
          options={{
            selection: true,
            pageSize: 10,
          }}
          actions={[
            {
              tooltip: 'Remove All Selected Users',
              icon: 'delete',
              onClick: (evt, sData) => {
                setOpenDelete(true);
                setSelectedData(sData);
              },
            },
          ]}
        />
      </div>
      <SaveDialog
        open={openSave}
        handleClose={handleSaveClose}
        columns={columns}
        data={data}
        saveTableData={saveTableData}
        table={table}
      />
      <DeleteDialog
        open={openDelete}
        data={selectedData}
        handleClose={handleDeleteClose}
        handleDeleteSelected={handleDeleteSelected}
      />
      <Backdrop className={classes.backdrop} open={openBD}>
        <CircularProgress color="inherit" />
      </Backdrop>
    </div>
  );
}
