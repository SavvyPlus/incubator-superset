import React from 'react';
import Button from '@material-ui/core/Button';
import MaterialTable from './materialTable';
import DeleteDialog from './DeleteDialog';
import PreLoader from '../../components/PreLoader';

export default function AssumptionTable({ version, table, tableData }) {
  const [fetching, setFetching] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [selctedData, setSelectedData] = React.useState([]);

  const [state, setState] = React.useState({
    columns: [
      { title: 'Name', field: 'name' },
      { title: 'Surname', field: 'surname' },
      { title: 'Birth Year', field: 'birthYear', type: 'numeric' },
      {
        title: 'Birth Place',
        field: 'birthCity',
      },
    ],
    data: [
      {
        name: 'Mehmet',
        surname: 'Baran',
        birthYear: 1987,
        birthCity: 'İstanbul',
      },
      {
        name: 'Zerya Betül',
        surname: 'Baran',
        birthYear: 2017,
        birthCity: 'Şanlıurfa',
      },
      {
        name: 'Ce2ya',
        surname: 'Mtren',
        birthYear: 2011,
        birthCity: 'Şanlıurfa',
      },
      {
        name: 'Colin',
        surname: 'Wang',
        birthYear: 1995,
        birthCity: 'İstanbul',
      },
    ],
    // columns: [],
    // data: [],
  });

  const handleFetchTableData = () => {};

  const handleDialogClose = () => {
    setOpen(false);
  };

  return (
    <div className="mb-50">
      <h3 className="mt-50">Step 4: Fetch Table Data</h3>
      <Button disabled={!version} variant="contained" color="primary">
        {fetching ? (
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
            emptyDataSourceMessage: 'Please fetch table data first',
          },
        }}
        columns={state.columns}
        data={state.data}
        editable={{
          onRowAdd: newData =>
            new Promise(resolve => {
              setTimeout(() => {
                resolve();
                setState(prevState => {
                  const data = [...prevState.data];
                  data.push(newData);
                  return { ...prevState, data };
                });
              }, 600);
            }),
          onRowUpdate: (newData, oldData) =>
            new Promise(resolve => {
              setTimeout(() => {
                resolve();
                if (oldData) {
                  setState(prevState => {
                    const data = [...prevState.data];
                    data[data.indexOf(oldData)] = newData;
                    return { ...prevState, data };
                  });
                }
              }, 600);
            }),
          onRowDelete: oldData =>
            new Promise(resolve => {
              setTimeout(() => {
                resolve();
                setState(prevState => {
                  const data = [...prevState.data];
                  data.splice(data.indexOf(oldData), 1);
                  return { ...prevState, data };
                });
              }, 600);
            }),
        }}
        options={{
          selection: true,
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
