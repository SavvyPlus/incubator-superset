import React from 'react';
import Button from '@material-ui/core/Button';
import MaterialTable from './materialTable';
import DeleteDialog from './DeleteDialog';
import PreLoader from '../../components/PreLoader';

export default function AssumptionTable({
  version,
  table,
  tableData,
  fetchingVersions,
  fetchTableData,
}) {
  const [fetchingData, setFetchingData] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [selctedData, setSelectedData] = React.useState([]);

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

  const handleFetchTableData = () => {
    setFetchingData(true);
    fetchTableData(table, version).then(() => {
      setFetchingData(false);
    });
  };

  const handleDialogClose = () => {
    setOpen(false);
  };

  const tableD = getTableData(tableData);

  return (
    <div className="mb-50">
      <h3 className="mt-50">Step 4: Fetch Table Data</h3>
      <Button
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
      <h3 className="mt-50">Step 5: Modify Your Table</h3>
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
                resolve();
                console.log('adding....');
              }, 600);
            }),
          onRowUpdate: (newData, oldData) =>
            new Promise(resolve => {
              setTimeout(() => {
                resolve();
                if (oldData) {
                  console.log('updating....');
                }
              }, 600);
            }),
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
      <DeleteDialog
        open={open}
        data={selctedData}
        handleClose={handleDialogClose}
      />
    </div>
  );
}
