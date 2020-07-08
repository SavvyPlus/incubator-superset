import React from 'react';
import Button from '@material-ui/core/Button';
import VersionSelect from './VersionSelect';
import MaterialTable from './materialTable';
import PreLoader from '../../components/PreLoader';

export default function AssumptionTable({ table, tableData }) {
  const [fetching, setFetching] = React.useState(false);
  const [state, setState] = React.useState({
    // columns: [
    //   { title: 'Name', field: 'name' },
    //   { title: 'Surname', field: 'surname' },
    //   { title: 'Birth Year', field: 'birthYear', type: 'numeric' },
    //   {
    //     title: 'Birth Place',
    //     field: 'birthCity',
    //     lookup: { 34: 'İstanbul', 63: 'Şanlıurfa' },
    //   },
    // ],
    // data: [
    //   { name: 'Mehmet', surname: 'Baran', birthYear: 1987, birthCity: 63 },
    //   {
    //     name: 'Zerya Betül',
    //     surname: 'Baran',
    //     birthYear: 2017,
    //     birthCity: 34,
    //   },
    // ],
    columns: [],
    data: [],
  });

  const handleFetchTableData = () => {};

  return (
    <div className="mb-50">
      <VersionSelect />
      <h3 className="mt-50">Step 4: Fetch Table Data</h3>
      <Button variant="contained" color="primary">
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
      />
    </div>
  );
}
